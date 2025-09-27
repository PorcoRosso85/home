package duplicate1
import "example.corp/contract-system/schema"

TestContract1: schema.Contract & {
    namespace: "corp.example"
    name:      "api-service"  // Same as existing
    role:      "service"
    provides:  []
    dependsOn: []
}
