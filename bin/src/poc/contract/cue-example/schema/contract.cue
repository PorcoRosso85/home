package schema

// Contract schema version for SemVer tracking
#SchemaVersion: "1.0.0"

// Closed contract structure - no additional fields allowed
#Contract: close({
	// Required identification fields
	namespace: #Namespace
	name:      #Name
	role:      #Role

	// Optional version for the contract itself
	version?: #SemVer

	// Capability declarations
	provides: [...#Capability]
	dependsOn: [...#CapabilityRef]

	// Optional ownership ranges
	ports?: [...#Port]
	portRanges?: [...#PortRange]

	// Optional metadata
	description?: string
	tags?: [...string]
})

// Namespace validation - reverse domain format
#Namespace: string & =~"^[a-z0-9.-]+$" & =~".+"

// Name validation - project name
#Name: string & =~"^[a-z0-9-]+$" & =~".+"

// Role enumeration - exactly these values allowed
#Role: "service" | "lib" | "infra" | "app" | "tool"

// Port number validation
#Port: int & >=1 & <=65535

// Port range validation
#PortRange: close({
	start: #Port
	end:   #Port
})

// SemVer pattern validation
#SemVer: string & =~"^[0-9]+\\.[0-9]+\\.[0-9]+(-[a-zA-Z0-9.-]+)?(\\+[a-zA-Z0-9.-]+)?$"

// Capability definition - what this contract provides
#Capability: close({
	// Required fields
	kind: #CapabilityKind

	// Optional identification
	id?: string

	// Optional version constraint
	version?: #SemVer

	// Network-specific fields
	port?:     #Port
	protocol?: #Protocol
	scope?:    #Scope

	// Optional metadata
	description?: string
})

// Capability reference - what this contract depends on
#CapabilityRef: close({
	// Required fields
	kind:   #CapabilityKind
	target: #Target

	// Optional identification and constraints
	id?:           string
	versionRange?: string

	// Optional metadata
	description?: string
	optional?:    bool
})

// Target format: namespace/name
#Target: string & =~"^[a-z0-9.-]+/[a-z0-9-]+$"

// Capability kind enumeration
#CapabilityKind: "http" | "grpc" | "db" | "queue" | "cache" | "storage" | "auth" | "monitoring" | "logging" | "config" | "secret" | "dns" | "proxy" | "gateway"

// Protocol enumeration
#Protocol: "tcp" | "udp" | "http" | "https" | "grpc" | "websocket"

// Scope enumeration
#Scope: "internal" | "public" | "private"

// Export the main contract schema definition
// Contract: #Contract  // Uncomment to instantiate
