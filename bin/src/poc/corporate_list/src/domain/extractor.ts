/**
 * Company name extraction logic for the corporate scraper
 */

import { EXTRACTION_CONFIG } from '../variables.js'

/**
 * Extract company name from text using configured patterns
 * Simple extraction with 60% accuracy target - prioritizing speed over precision
 * @param text - Text to extract company name from
 * @returns Extracted company name or null if not found
 */
export function extractCompanyName(text: string): string | null {
  if (!text) return null
  
  // Use patterns from configuration
  const patterns = EXTRACTION_CONFIG.companyPatterns
  
  for (const pattern of patterns) {
    const match = text.match(pattern)
    if (match) {
      return match[0].trim()
    }
  }
  
  return null // No match found - that's OK with 60% target accuracy
}

/**
 * Extract multiple company names from text
 * @param text - Text to extract company names from
 * @returns Array of extracted company names
 */
export function extractAllCompanyNames(text: string): string[] {
  if (!text) return []
  
  const companies: string[] = []
  const patterns = EXTRACTION_CONFIG.companyPatterns
  
  for (const pattern of patterns) {
    const matches = text.match(new RegExp(pattern, 'g'))
    if (matches) {
      companies.push(...matches.map(m => m.trim()))
    }
  }
  
  // Remove duplicates while preserving order
  return [...new Set(companies)]
}

/**
 * Check if text likely contains a company name
 * @param text - Text to check
 * @returns True if text likely contains a company name
 */
export function containsCompanyName(text: string): boolean {
  return extractCompanyName(text) !== null
}