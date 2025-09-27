package duplicate2
import "example.corp/contract-system/schema"

TestContract2: schema.Contract & {
    namespace: "corp.example"
    name:      "api-service"  // Duplicate name
    role:      "lib"
    provides:  []
    dependsOn: []
}
