/**
 * Tweet reading functionality
 * Provides functions to fetch tweets from Twitter API
 */

import { createClient } from './client';

/**
 * Tweet data interface
 */
export interface Tweet {
  id: string;
  text: string;
  author_id?: string;
  created_at?: string;
  public_metrics?: {
    retweet_count: number;
    like_count: number;
    reply_count: number;
    quote_count: number;
  };
}

/**
 * Fetch a tweet by ID
 * @param id Tweet ID to fetch
 * @returns Promise resolving to tweet data
 * @throws Error if tweet cannot be fetched or doesn't exist
 */
export async function getTweet(id: string): Promise<Tweet> {
  if (!id || typeof id !== 'string' || id.trim() === '') {
    throw new Error('Tweet ID must be a non-empty string');
  }

  try {
    const client = createClient();
    
    const response = await client.tweets.findTweetById(id, {
      'tweet.fields': ['author_id', 'created_at', 'public_metrics']
    });
    
    if (!response.data) {
      throw new Error(`Tweet with ID ${id} not found`);
    }
    
    return {
      id: response.data.id,
      text: response.data.text,
      author_id: response.data.author_id,
      created_at: response.data.created_at,
      public_metrics: response.data.public_metrics
    };
  } catch (error) {
    if (error instanceof Error) {
      // Re-throw known errors
      throw error;
    }
    
    // Handle unknown errors
    throw new Error(`Failed to fetch tweet: ${String(error)}`);
  }
}