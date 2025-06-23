Welcome to the Wētā FX internal readme for Embree
=================================================

This repo is activly synced from [The OSS upstream (external)](https://github.com/RenderKit/embree). 
It is also possible to push changes to the [Wētā FX external fork](https://github.com/wetadigital/embree), allowing 
for contributions to flow back to the OSS repo (via Pull Request).


Legalities
----------

While not all commits to this repo will be committed back to the opensource community, it is easier if we assume that they are.
This makes it easier to push commits at a later date if we do decide to contribute them etc.

Therefore, all commits *must* include a  [Developer Certificate of Origin (DCO)](https://wiki.linuxfoundation.org/dco) 
sign off. This certifies that you agree to the terms at https://developercertificate.org/. In short, it states you wrote the code 
yourself without copying / transcribing it from somewhere.

This should be done using your Wētā FX username and email address:
For example:

`Signed-off-by: Jane Doe <jdoe@wetafx.co.nz>`

> **TIP:** You can apply a DCO signoff using the following git commit command:
> ```bash
> git commit -m "Test" --signoff
> ```

Wētā FX DOES NOT HAVE a signed contributor agreement (CLA) in place.

As a company, we will also be adding the review chain to that contribution (much like the linux kernel does 
where at the end of a commit comment, you will see a chain of Signed-off-by), which should provide confidence for the 
upstream project to accept it more readily.

Brand new files that are added as part of adding a feature shall include a copyright notice as a comment as the first line. 
Additionally, an SPDX License Identifier (see https://spdx.org) or similar that is appropriate for that project should be 
added in accordance with the upstream project policies. Something like the following for C++

```c++
// Copyright © 2024, Wētā FX, Ltd.
// SPDX-License-Identifier: Apache-2.0
```

Namespacing
-----------

All git tags and branches created internally should be prefixed with `weta/`. This avoids collisions with upstream refs.

Workflow
--------

As we have changes that are internal only, we have a `weta/main` branch. This 
functions like the `main` branch would in any other repo, but will be updated with the upstream from time to time.

Due to the syncing nature of this, there are a few branches that we maintain

* `weta/main` - the internal main branch, with all our internal only changes.
* `weta/RB-X.Y.Z` - this is the branch for a specific release of Embree, and is branched off the upstream release tag. It allows patches to be made for that release.
* `weta/public/$BRANCHNAME` - Branches that are synced to the Wētā FX external fork. 
* `weta/user/$USERNAME/$BRANCHNAME` - This is your working branch. It should branch off `weta/main` or `weta/RB-X.Y.Z`

At the moment, only repo maintainers can merge into the first 3 branch types. We will look at opening that up as we get more familir with this process and work out any issues.

To make a change, make a `weta/user/$USERNAME/$BRANCHNAME` branch off either `weta/main` (most common) or `weta/RB-X.Y.Z` (To patch a specific release).


Local Merges
------------

Once your changes have been made, you can merge these back into the weta internal branches like normal. That is, you can push up an MR, have it reviwed and merged!


Pushing Changes to Upstream
---------------------------

If your change should be contributed back to the OSS repo, then flag that in your Merge request. A maintainer will need to cherry-pick those changes into a `weta/public/$BRANCHNAME`
that is based off of main, so they can sync to the [Wētā FX external fork](https://github.com/wetadigital/embree).

Once this branch is created, a Pull Request can be made via the [Wētā FX external fork](https://github.com/wetadigital/embree) targeting the OSS repo. Ideally, this is done by 
the dev who did the work. This will require you to have a gitlab account with your wetafx email address. 

If you do not have one setup, a maintainer _might_ do it for you if you ask nicely!


How to build & compile
----------------------

# TODO


How to release
--------------

# TODO
     
