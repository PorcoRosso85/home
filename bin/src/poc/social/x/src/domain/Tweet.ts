/**
 * Tweet domain value object
 * Pure domain logic with validation rules and no external dependencies
 */

export interface TweetPublicMetrics {
  retweet_count: number;
  like_count: number;
  reply_count: number;
  quote_count: number;
}

export interface TweetData {
  id: string;
  text: string;
  author_id?: string;
  created_at?: string;
  public_metrics?: TweetPublicMetrics;
}

/**
 * Tweet value object representing a Twitter post
 * Encapsulates validation rules and domain behavior
 */
export class Tweet {
  private constructor(
    private readonly _id: string,
    private readonly _text: string,
    private readonly _author_id?: string,
    private readonly _created_at?: string,
    private readonly _public_metrics?: TweetPublicMetrics
  ) {}

  /**
   * Factory method to create a Tweet from raw data
   * @param data Raw tweet data
   * @returns Tweet instance
   * @throws Error if data is invalid
   */
  static fromData(data: TweetData): Tweet {
    if (!Tweet.isValidId(data.id)) {
      throw new Error('Tweet ID must be a non-empty string');
    }
    
    if (!Tweet.isValidText(data.text)) {
      throw new Error('Tweet text must be a non-empty string');
    }

    return new Tweet(
      data.id,
      data.text,
      data.author_id,
      data.created_at,
      data.public_metrics
    );
  }

  /**
   * Validates if a tweet ID is valid
   * @param id Tweet ID to validate
   * @returns true if valid, false otherwise
   */
  static isValidId(id: unknown): id is string {
    return typeof id === 'string' && id.trim().length > 0;
  }

  /**
   * Validates if tweet text is valid
   * @param text Tweet text to validate
   * @returns true if valid, false otherwise
   */
  static isValidText(text: unknown): text is string {
    return typeof text === 'string' && text.trim().length > 0;
  }

  /**
   * Get tweet ID
   */
  get id(): string {
    return this._id;
  }

  /**
   * Get tweet text
   */
  get text(): string {
    return this._text;
  }

  /**
   * Get author ID if available
   */
  get author_id(): string | undefined {
    return this._author_id;
  }

  /**
   * Get creation timestamp if available
   */
  get created_at(): string | undefined {
    return this._created_at;
  }

  /**
   * Get public metrics if available
   */
  get public_metrics(): TweetPublicMetrics | undefined {
    return this._public_metrics;
  }

  /**
   * Convert tweet to JSON representation
   * @returns Tweet data as plain object
   */
  toJSON(): TweetData {
    return {
      id: this._id,
      text: this._text,
      author_id: this._author_id,
      created_at: this._created_at,
      public_metrics: this._public_metrics
    };
  }

  /**
   * Compare tweets for equality
   * @param other Other tweet to compare
   * @returns true if tweets are equal
   */
  equals(other: Tweet): boolean {
    return this._id === other._id;
  }
}