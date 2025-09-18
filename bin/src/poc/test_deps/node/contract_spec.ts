// 契約ベースの仕様定義サンプル

// 基本的な契約インターフェース
interface ContractSpec {
  // 非同期処理の契約
  async?: {
    timeout: number;        // ミリ秒
    retryable: boolean;     // リトライ可能か
  };
  
  // 前提条件・事後条件
  conditions?: {
    pre: string[];          // 実行前に満たすべき条件
    post: string[];         // 実行後に保証される条件
  };
  
  // 権限の契約
  auth?: {
    required: boolean;
    roles?: string[];       // 必要なロール
  };
  
  // エラーハンドリング契約
  errors?: {
    [errorType: string]: string;  // エラータイプと説明
  };
}

// ユーザー作成の契約仕様
export const createUserContract: ContractSpec = {
  async: {
    timeout: 5000,
    retryable: false
  },
  conditions: {
    pre: [
      "email must be unique",
      "password must be 8+ chars"
    ],
    post: [
      "user exists in database",
      "user.id is generated",
      "user.createdAt is set"
    ]
  },
  auth: {
    required: true,
    roles: ["admin", "manager"]
  },
  errors: {
    "DUPLICATE_EMAIL": "Email already exists",
    "WEAK_PASSWORD": "Password too weak",
    "UNAUTHORIZED": "No permission to create users"
  }
};

// より複雑な例：注文処理の契約
export const processOrderContract: ContractSpec = {
  async: {
    timeout: 30000,
    retryable: true
  },
  conditions: {
    pre: [
      "cart.items.length > 0",
      "payment.method is valid",
      "inventory sufficient for all items"
    ],
    post: [
      "order.status = 'confirmed'",
      "payment.charged = true",
      "inventory.reduced",
      "email.sent to customer"
    ]
  },
  auth: {
    required: true,
    roles: ["customer", "admin"]
  },
  errors: {
    "INSUFFICIENT_INVENTORY": "Some items out of stock",
    "PAYMENT_FAILED": "Payment processing failed",
    "INVALID_ADDRESS": "Shipping address invalid"
  }
};