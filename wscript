#! /usr/bin/env python
""" Wētā FX build definition and execution
"""
import collections

import oz
import waflib.Configure


def options(opt):
    opt.load("wak.tools")
    opt.load("compiler_cxx")
    opt.load("buildmatrix_wak")


@waflib.Configure.conf
def build_requirement_range(conf: waflib.Configure.ConfigurationContext, lower_bound: str, limit: str):
    """ Get an oz requirement range using the version of an app in the configured environment as a lower bound
    and the provided ``limit`` to determine the upper bound.

    This range can then be used in makePak so the pak requires the appropriate versions based on what we built against.

    Args:
        conf: The current wak configuration context.
        lower_bound: The minimum version supported by the requirement
        limit: Which semantic version component to use as the upper bound of the requirement range.
            This can be one of "major", "minor", or "patch".
            For example, if the build env contains version "1.2.3" and limit="major" then the result range 
            will be "1.2.3<2" whereas limit="minor" would result in "1.2.3<1.3"

    Returns:
        A requirement range like "1.2.3<2" where the version in ``build_env`` is used as the lower bound 
        and ``limit`` is used to determine the upper bound.
    """
    # Get the major, minor, and patch components of the lower bound semantic version
    #
    # Note that special care must be taken to account for lower bounds that don't 
    # specify all three major, minor, and patch numbers. For example, if the lower 
    # bound is just "1.80" then we want major=1, minor=80, and patch=0.
    # 
    # Similarly we need to account for cases where the version is over-specified 
    # like "1.2.3.4" in which case we want to simply strip the last number off
    version = oz.Version(lower_bound)
    major_minor_patch = [0, 0, 0]
    for i, c in enumerate(version.components[:3]):
        if not c.is_int:
            # e.g. "usd-23.08-weta.1" the "patch" component would technically be "weta" but
            # we'll just ignore that and treat it as 0
            break
        major_minor_patch[i] = c.value
    major, minor, patch = major_minor_patch

    # Construct an upper bound based on the provided ``limit``
    limit = str(limit).lower()
    if limit == "major":
        upper_bound = str(major + 1)
    elif limit == "minor":
        upper_bound = f"{major}.{minor + 1}"
    elif limit == "patch":
        upper_bound = f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"expected `limit` arg to be 'major', 'minor', or 'patch': {limit!r}")

    return "{}<{}".format(lower_bound, upper_bound)


@waflib.Configure.conf
def build_requirement_range_from_env(conf: waflib.Configure.ConfigurationContext, app: str, limit: str):
    """ Get an oz requirement range using the version of an app in the configured environment as a lower bound
    and the provided ``limit`` to determine the upper bound.

    This range can then be used in makePak so the pak requires the appropriate versions based on what we built against.

    Args:
        conf: The current wak configuration context.
        app: The oz app to build a requirement range for
        limit: Which semantic version component to use as the upper bound of the requirement range.
            This can be one of "major", "minor", or "patch".
            For example, if the build env contains version "1.2.3" and limit="major" then the result range 
            will be "1.2.3<2" whereas limit="minor" would result in "1.2.3<1.3"

    Returns:
        A requirement range like "1.2.3<2" where the version in ``build_env`` is used as the lower bound 
        and ``limit`` is used to determine the upper bound.
    """
    all_paks = oz.Oz.get_app_versions_from_oz_env(conf.env.env)
    pak_lut = dict([oz.AppVersion.split_name(pak) for pak in all_paks])
    if app not in pak_lut:
        raise EnvironmentError(f"Could not find {app} in build env")
    lower_bound = pak_lut[app]
    return conf.build_requirement_range(lower_bound, limit)


def configure(conf):
    conf.env.WAK_NON_CI_RELEASE_CMDS = ["tag"]

    conf.load("wak.tools")
    conf.load("wak.tools.deploySource")
    conf.load("buildmatrix_wak")

    # Checkout the build in the release dir and run the build from there.
    # This ensures that the source is deployed alongside the code, and allows the debug information to contain
    # actual file paths.
    conf.env.WAK_STAGED_RELEASE = "1"
    conf.env.WAK_STAGED_RELEASE_SRC = "1"
    conf.env.WAK_STAGED_RELEASE_BASE = "/digi/src/"
    conf.env.WAK_STAGED_RELEASE_SRC_GROUP = "dev"
    conf.env.WAK_STAGED_RELEASE_SRC_PERMS = "0444"

    # Setup build variants for each VFX Platform and run cmakeGenerate for each
    requirement_ranges = collections.defaultdict(list)
    for variant in conf.buildmatrix_make_variants("WetaVFXPlatform"):
        conf.buildmatrix_oz(
            area="/", 
            limits=[
                # Use platform-specific version of gcc rather than the system version.
                # The WetaVFXPlatform variant will choose the correct version of gcc for us 
                # but that's a soft requirement so we do need to explicitly add gcc to the env like this.
                # NOTE: the gcc pak also provides default compiler flags
                "gcc",

                "cmake",
                "ninja",
                "weta_cmake_provider",
                "tbb",
            ]
        )
        
        # accumulate ranges for pak requirements that we'll pass to makeLibPak below
        requirement_ranges["WetaVFXPlatform"].append(conf.build_requirement_range_from_env("WetaVFXPlatform", limit="major"))
        requirement_ranges["tbb"].append(conf.build_requirement_range_from_env("tbb", limit="minor"))

        # generate cmake files to build later
        conf.load("compiler_cxx")
        conf.load("wak.tools.cmake")
        conf.buildmatrix_set_flags(flavor_override="opt")
        conf.cmakeGenerate(
            # wak defaults this to ON but that causes the following problem in this project
            # so we've set it to OFF explicitly::
            #
            #   CMake Error at common/sys/CMakeLists.txt:23 (TARGET_LINK_LIBRARIES):
            #     Target "sys" has LINK_LIBRARIES_ONLY_TARGETS enabled, but it links to:
            #   
            #       dl
            #   
            #     which is not a target.  Possible reasons include:
            #   
            #       * There is a typo in the target name.
            #       * A find_package call is missing for an IMPORTED target.
            #       * An ALIAS target is missing.
            #
            # TODO: remove this and fix common/sys/CMakeLists.txt?
            CMAKE_LINK_LIBRARIES_ONLY_TARGETS="OFF",

            BUILD_TESTING="OFF",
            BUILD_DOC="OFF",
            EMBREE_STATIC_LIB="OFF",
            EMBREE_ISPC_SUPPORT="OFF",
            EMBREE_ZIP_MODE="OFF",
            EMBREE_TUTORIALS="OFF",
            EMBREE_INSTALL_DEPENDENCIES="OFF",
            EMBREE_STAT_COUNTERS="OFF",
            EMBREE_STACK_PROTECTOR="OFF",
            EMBREE_RAY_MASK="OFF",
            EMBREE_BACKFACE_CULLING="OFF",
            EMBREE_FILTER_FUNCTION="ON",
            EMBREE_IGNORE_INVALID_RAYS="OFF",
            EMBREE_COMPACT_POLYS="OFF",
            EMBREE_GEOMETRY_TRIANGLE="ON",
            EMBREE_GEOMETRY_QUAD="ON",
            EMBREE_GEOMETRY_CURVE="ON",
            EMBREE_GEOMETRY_SUBDIVISION="ON",
            EMBREE_GEOMETRY_USER="ON",
            EMBREE_GEOMETRY_INSTANCE="ON",
            EMBREE_GEOMETRY_GRID="ON",
            EMBREE_GEOMETRY_POINT="ON",
            EMBREE_RAY_PACKETS="ON",
            EMBREE_MAX_INSTANCE_LEVEL_COUNT="4",
            EMBREE_CURVE_SELF_INTERSECTION_AVOIDANCE_FACTOR="2.0",
            EMBREE_MIN_WIDTH="ON",
        )

    # Make the lib pak
    conf.makeLibPak(
        name=conf.env.WAK_APP_NAME,
        version=conf.env.WAK_APP_VERSION,
        prefix="",  # remove "lib" prefix
        type="shared",  # TODO: figure out how to deploy both shared and static
        includes="${PREFIX}/WetaVFXPlatform-%(WETA_VFXPLATFORM_ID)s/include",
        lib="embree3",
        libpath=["${PREFIX}/WetaVFXPlatform-%(WETA_VFXPLATFORM_ID)s/lib"],
        requires={
            "WetaVFXPlatform": {"ver_range": "|".join(requirement_ranges["WetaVFXPlatform"])},
            "tbb": {"ver_range": "|".join(requirement_ranges["tbb"])},
        },
        variables={
            "LD_LIBRARY_PATH": {
                "value": "${PREFIX}/WetaVFXPlatform-%(WETA_VFXPLATFORM_ID)s/lib",
                "action": "env_prp",
            }
        },
        buildRequires={
            "WetaVFXPlatform": {"ver_range": "|".join(requirement_ranges["WetaVFXPlatform"])},
            "tbb": {"ver_range": "|".join(requirement_ranges["tbb"])},
        },
        buildActions={
            "Embree_ROOT": {
                "value": "${PREFIX}/WetaVFXPlatform-%(WETA_VFXPLATFORM_ID)s",
                "action": "env_set",
                "intended_for": "cmake",
            }
        },
    )

    # Create a "libembree" forwarding pak
    # 
    # Previously the embree pak was called "libembree" but we've decided to do away with the "lib" prefix.
    # See https://adrs.wetafx.co.nz/projects/build-test-deployment/0005/
    #
    # This forwarding pak is meant as a transition step since there are paks out there which have a requirement 
    # on "libembree" so if we were to release "embree" those requirements would be invalid until all those other paks
    # can be updated. By creating a forwarding pak that simply requires the real "embree" pak we're able to release
    # embree and still satisfy the old "libembree" requirements until those paks have been updated.
    #
    # TODO: remove this forwarding pak and deprecate all of its versions once requirements in all dependent pak have
    #       been updated to require "embree" instead of "libembree"
    if conf.isRelease():
        runtime_requirement_range = conf.build_requirement_range(lower_bound=conf.env.WAK_APP_VERSION, limit="patch")
        conf.makePak(
            appName=f"lib{conf.env.WAK_APP_NAME}",
            requires={conf.env.WAK_APP_NAME: {"ver_range": runtime_requirement_range}},
            buildRequires={conf.env.WAK_APP_NAME: {"ver_range": runtime_requirement_range}},
        )


def build(bld):
    for _ in bld.iterVariants(category="WetaVFXPlatform"):
        build_task = bld.cmakeBuild(name="build")
        bld.cmakeInstall(name="install", dependsOn=[build_task])

    if bld.isRelease():
        bld.setOzAppDetails(
            app=bld.env.WAK_APP_NAME,
            options={
                "contacts": {
                    "Department": "Engineering",
                    "Maintainer": "tpitts@wetafx.co.nz",
                },
                "description": "Open source collection of high-performance ray tracing kernels developed at Intel",
                "info": {
                    "JIRA": f"https://jira.wetafx.co.nz/projects/HABITAT",
                    "Teams": "https://teams.microsoft.com/l/channel/19%3A9464d1bfef714b7cb94b88c7feaa86fc%40thread.skype/build-test-deployment?groupId=b544b9ae-752e-45f6-843d-49fb0317a731&tenantId=5ecba919-6cf8-411b-a462-db882331fd21",
                },
                "third_party": True,
                "license": "Apache-2.0",
            },
            description="set/refresh the app metadata",
        )
