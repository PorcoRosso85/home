package contracts

// Sample flake contract (simplified for testing)
_contract: {
	role:  "app"
	owner: "test-user"
	exports: [
		{
			kind:        "cli"
			id:          "hello"
			description: "Sample hello world CLI application"
			scope:       "public"
		},
	]
	dependsOn: []
}
