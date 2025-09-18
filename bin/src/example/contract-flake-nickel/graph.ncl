# Contract Graph Visualization
# Defines nodes, edges, and metadata for flake dependency graphs

let NodeType = [| 'Producer, 'Transformer, 'Consumer |] in
let EdgeType = [| 'Dependency, 'Transform |] in

let Node = {
  id | String,
  type | NodeType,
  contract | {
    input | Array String,
    output | Array String,
    version | String,
  },
  metadata | {
    description | String,
    maintainer | String,
    created | String,
  }
} in

let Edge = {
  from | String,
  to | String,
  type | EdgeType,
  contract_requirements | Array String,
} in

let Graph = {
  nodes | Array Node,
  edges | Array Edge,
  metadata | {
    name | String,
    version | String,
    description | String,
  }
} in

# Basic contract graph with producer, transformer, consumer
let basic_graph = {
  nodes = [
    {
      id = "producer",
      type = 'Producer,
      contract = {
        input = [],
        output = ["data", "metrics"],
        version = "1.0.0",
      },
      metadata = {
        description = "Data producer flake",
        maintainer = "team@example.com",
        created = "2024-01-01",
      }
    },
    {
      id = "transformer",
      type = 'Transformer,
      contract = {
        input = ["data"],
        output = ["processed_data", "logs"],
        version = "1.2.0",
      },
      metadata = {
        description = "Data transformation flake",
        maintainer = "team@example.com",
        created = "2024-01-15",
      }
    },
    {
      id = "consumer",
      type = 'Consumer,
      contract = {
        input = ["processed_data", "logs"],
        output = [],
        version = "2.0.0",
      },
      metadata = {
        description = "Data consumer flake",
        maintainer = "team@example.com",
        created = "2024-02-01",
      }
    }
  ],
  edges = [
    {
      from = "producer",
      to = "transformer",
      type = 'Dependency,
      contract_requirements = ["data"],
    },
    {
      from = "transformer",
      to = "consumer",
      type = 'Transform,
      contract_requirements = ["processed_data", "logs"],
    }
  ],
  metadata = {
    name = "basic_contract_graph",
    version = "1.0.0",
    description = "Basic producer-transformer-consumer graph",
  }
} | Graph in

# Large-scale simulation with 10+ flakes
let large_scale_graph = {
  nodes = [
    # Data Sources
    {
      id = "data_source_a",
      type = 'Producer,
      contract = {
        input = [],
        output = ["raw_data_a"],
        version = "1.0.0",
      },
      metadata = {
        description = "Primary data source A",
        maintainer = "data-team@example.com",
        created = "2024-01-01",
      }
    },
    {
      id = "data_source_b",
      type = 'Producer,
      contract = {
        input = [],
        output = ["raw_data_b"],
        version = "1.1.0",
      },
      metadata = {
        description = "Secondary data source B",
        maintainer = "data-team@example.com",
        created = "2024-01-05",
      }
    },
    {
      id = "config_provider",
      type = 'Producer,
      contract = {
        input = [],
        output = ["config", "secrets"],
        version = "2.0.0",
      },
      metadata = {
        description = "Configuration and secrets provider",
        maintainer = "ops-team@example.com",
        created = "2024-01-10",
      }
    },
    
    # Preprocessing Layer
    {
      id = "preprocessor_a",
      type = 'Transformer,
      contract = {
        input = ["raw_data_a", "config"],
        output = ["cleaned_data_a"],
        version = "1.5.0",
      },
      metadata = {
        description = "Data A preprocessing pipeline",
        maintainer = "ml-team@example.com",
        created = "2024-01-15",
      }
    },
    {
      id = "preprocessor_b",
      type = 'Transformer,
      contract = {
        input = ["raw_data_b", "config"],
        output = ["cleaned_data_b"],
        version = "1.3.0",
      },
      metadata = {
        description = "Data B preprocessing pipeline",
        maintainer = "ml-team@example.com",
        created = "2024-01-20",
      }
    },
    
    # Feature Engineering
    {
      id = "feature_engineer",
      type = 'Transformer,
      contract = {
        input = ["cleaned_data_a", "cleaned_data_b"],
        output = ["features", "feature_metadata"],
        version = "2.1.0",
      },
      metadata = {
        description = "Feature engineering pipeline",
        maintainer = "ml-team@example.com",
        created = "2024-02-01",
      }
    },
    
    # Model Training
    {
      id = "model_trainer",
      type = 'Transformer,
      contract = {
        input = ["features", "config"],
        output = ["trained_model", "training_metrics"],
        version = "3.0.0",
      },
      metadata = {
        description = "ML model training pipeline",
        maintainer = "ml-team@example.com",
        created = "2024-02-10",
      }
    },
    
    # Model Validation
    {
      id = "model_validator",
      type = 'Transformer,
      contract = {
        input = ["trained_model", "features"],
        output = ["validation_results", "model_report"],
        version = "1.8.0",
      },
      metadata = {
        description = "Model validation and testing",
        maintainer = "qa-team@example.com",
        created = "2024-02-15",
      }
    },
    
    # Deployment
    {
      id = "model_deployer",
      type = 'Transformer,
      contract = {
        input = ["trained_model", "validation_results", "secrets"],
        output = ["deployed_service", "deployment_logs"],
        version = "2.5.0",
      },
      metadata = {
        description = "Model deployment service",
        maintainer = "ops-team@example.com",
        created = "2024-02-20",
      }
    },
    
    # Monitoring and Analytics
    {
      id = "monitor",
      type = 'Consumer,
      contract = {
        input = ["deployment_logs", "training_metrics"],
        output = [],
        version = "1.7.0",
      },
      metadata = {
        description = "System monitoring and alerting",
        maintainer = "ops-team@example.com",
        created = "2024-02-25",
      }
    },
    {
      id = "analytics_dashboard",
      type = 'Consumer,
      contract = {
        input = ["model_report", "feature_metadata", "validation_results"],
        output = [],
        version = "2.2.0",
      },
      metadata = {
        description = "Analytics and reporting dashboard",
        maintainer = "product-team@example.com",
        created = "2024-03-01",
      }
    },
    
    # API Gateway
    {
      id = "api_gateway",
      type = 'Consumer,
      contract = {
        input = ["deployed_service", "config"],
        output = [],
        version = "3.1.0",
      },
      metadata = {
        description = "External API gateway",
        maintainer = "api-team@example.com",
        created = "2024-03-05",
      }
    }
  ],
  edges = [
    # Data flow from sources to preprocessors
    {
      from = "data_source_a",
      to = "preprocessor_a",
      type = 'Dependency,
      contract_requirements = ["raw_data_a"],
    },
    {
      from = "data_source_b",
      to = "preprocessor_b",
      type = 'Dependency,
      contract_requirements = ["raw_data_b"],
    },
    {
      from = "config_provider",
      to = "preprocessor_a",
      type = 'Dependency,
      contract_requirements = ["config"],
    },
    {
      from = "config_provider",
      to = "preprocessor_b",
      type = 'Dependency,
      contract_requirements = ["config"],
    },
    
    # Preprocessed data to feature engineering
    {
      from = "preprocessor_a",
      to = "feature_engineer",
      type = 'Transform,
      contract_requirements = ["cleaned_data_a"],
    },
    {
      from = "preprocessor_b",
      to = "feature_engineer",
      type = 'Transform,
      contract_requirements = ["cleaned_data_b"],
    },
    
    # Features to model training
    {
      from = "feature_engineer",
      to = "model_trainer",
      type = 'Transform,
      contract_requirements = ["features"],
    },
    {
      from = "config_provider",
      to = "model_trainer",
      type = 'Dependency,
      contract_requirements = ["config"],
    },
    
    # Model validation
    {
      from = "model_trainer",
      to = "model_validator",
      type = 'Transform,
      contract_requirements = ["trained_model"],
    },
    {
      from = "feature_engineer",
      to = "model_validator",
      type = 'Dependency,
      contract_requirements = ["features"],
    },
    
    # Model deployment
    {
      from = "model_trainer",
      to = "model_deployer",
      type = 'Transform,
      contract_requirements = ["trained_model"],
    },
    {
      from = "model_validator",
      to = "model_deployer",
      type = 'Transform,
      contract_requirements = ["validation_results"],
    },
    {
      from = "config_provider",
      to = "model_deployer",
      type = 'Dependency,
      contract_requirements = ["secrets"],
    },
    
    # Monitoring and analytics
    {
      from = "model_deployer",
      to = "monitor",
      type = 'Transform,
      contract_requirements = ["deployment_logs"],
    },
    {
      from = "model_trainer",
      to = "monitor",
      type = 'Transform,
      contract_requirements = ["training_metrics"],
    },
    {
      from = "model_validator",
      to = "analytics_dashboard",
      type = 'Transform,
      contract_requirements = ["model_report", "validation_results"],
    },
    {
      from = "feature_engineer",
      to = "analytics_dashboard",
      type = 'Transform,
      contract_requirements = ["feature_metadata"],
    },
    
    # API Gateway
    {
      from = "model_deployer",
      to = "api_gateway",
      type = 'Transform,
      contract_requirements = ["deployed_service"],
    },
    {
      from = "config_provider",
      to = "api_gateway",
      type = 'Dependency,
      contract_requirements = ["config"],
    }
  ],
  metadata = {
    name = "ml_pipeline_graph",
    version = "1.0.0",
    description = "Large-scale ML pipeline with 13 flakes",
  }
} | Graph in

# Export both graphs
{
  basic = basic_graph,
  large_scale = large_scale_graph,
}