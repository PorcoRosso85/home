# AppArmor profile for similarity tool
# This restricts the similarity tools to read-only access

# Include base abstractions
#include <abstractions/base>

# Git repository access (read-only)
/**.git/** r,
/.git/** r,

# Source code files (read-only)
/**.rs r,
/**.py r,
/**.ts r,
/**.js r,
/**.tsx r,
/**.jsx r,
/**.go r,
/**.java r,
/**.c r,
/**.cpp r,
/**.h r,
/**.hpp r,

# Cargo/Rust specific
@{HOME}/.cargo/** r,
@{HOME}/.rustup/** r,
/usr/bin/cargo ix,
/usr/bin/rustc ix,

# Temporary files
/tmp/** rw,
/var/tmp/** rw,

# Process execution
/usr/bin/git ix,
/bin/sh ix,
/bin/bash ix,

# Deny dangerous operations
deny @{HOME}/.ssh/** rw,
deny /etc/** w,
deny network,