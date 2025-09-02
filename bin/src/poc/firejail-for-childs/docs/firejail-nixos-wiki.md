# Firejail on NixOS (from nixos.wiki)

Source: https://nixos.wiki/wiki/Firejail
Retrieved: 2025-09-02

## Overview

Firejail is a SUID sandbox program that reduces the risk of security breaches by restricting the running environment of untrusted applications using Linux namespaces, seccomp-bpf and Linux capabilities.

## Installation

### Basic Installation
```nix
programs.firejail.enable = true;
```

### Advanced Configuration with Wrapped Binaries
```nix
programs.firejail = {
  enable = true;
  wrappedBinaries = {
    librewolf = {
      executable = "${pkgs.librewolf}/bin/librewolf";
      profile = "${pkgs.firejail}/etc/firejail/librewolf.profile";
      extraArgs = [
        # ignore brave.local and use globals.local + librewolf.local
        "--ignore=private-dev"
        # add any extra args you need
        "--env=GTK_THEME=Adwaita:dark"
      ];
    };
  };
};
```

## Basic Usage

### Launch a Sandboxed Shell
```bash
firejail bash
```

### Launch Application with Profile
```bash
firejail --profile=$(nix ...) firefox
```

## Profile Customization

### Using .local Files
Firejail supports local customization files to extend existing profiles without modifying the original:
- Create `.local` files to add custom rules
- These files can override or extend default profiles
- Location: typically in user's home directory or system config

### Custom Profile Creation
For applications without existing profiles:
1. Create a new profile file
2. Define restrictions and permissions
3. Reference the profile when launching the application

## Advanced Features

### Network Isolation
- Complete network isolation possible
- Can restrict network access per application
- Supports both blacklist and whitelist approaches

### Tor Routing
- Route application traffic through Tor
- Provides additional privacy layer
- Configurable per application

### Desktop Integration
- Add desktop icons for Firejailed applications
- Integrate sandboxed apps seamlessly into desktop environment
- Maintain user experience while improving security

## NixOS-Specific Considerations

### SUID Requirements
- Firejail requires SUID permissions to function
- NixOS handles this through the `programs.firejail` module
- Manual SUID configuration not recommended

### Nix Store Integration
- Profiles can reference Nix store paths
- Use Nix expressions for dynamic path resolution
- Ensures reproducibility across systems

### Declarative Configuration
- All Firejail settings can be managed declaratively
- Configuration in `/etc/nixos/configuration.nix`
- Changes apply on system rebuild

## Common Use Cases

### Web Browser Sandboxing
```nix
programs.firejail.wrappedBinaries = {
  firefox = {
    executable = "${pkgs.firefox}/bin/firefox";
    profile = "${pkgs.firejail}/etc/firejail/firefox.profile";
  };
};
```

### Development Environment Isolation
- Isolate development tools
- Prevent access to production credentials
- Limit filesystem access to project directories

### Untrusted Application Execution
- Run downloaded software safely
- Test potentially malicious code
- Isolate proprietary applications

## Troubleshooting

### Permission Denied Errors
- Ensure `programs.firejail.enable = true` is set
- Check SUID permissions are correctly applied
- Verify user is not in restricted groups

### Profile Not Found
- Check profile path in Nix store
- Ensure profile package is installed
- Use absolute paths for custom profiles

### Application Functionality Issues
- Some applications may break with strict sandboxing
- Use `--ignore` flags to selectively disable restrictions
- Check application logs for specific errors

## Best Practices

1. **Start with existing profiles**: Use and extend default profiles when available
2. **Test incrementally**: Add restrictions gradually to identify breaking points
3. **Use .local files**: Keep customizations separate from default profiles
4. **Document changes**: Maintain notes on why specific restrictions were added/removed
5. **Regular updates**: Keep Firejail and profiles updated for security patches

## Additional Resources

- Official Firejail documentation
- NixOS manual section on Firejail
- Community-maintained profile repository
- Security-focused NixOS configurations