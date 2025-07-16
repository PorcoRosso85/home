#!/usr/bin/env -S deno run --allow-net --allow-read

// Simple test to verify schema transformation works correctly
import { Transformer } from "../src/transformer.ts";

const transformer = new Transformer();

// Test data
const dashboardData = { city: "Tokyo" };
const weatherResponse = { temperature: 25.5, humidity: 60, location: "Tokyo" };

console.log("=== Schema Transformation Test ===");
console.log("Dashboard sends:", dashboardData);

// Forward transform (Dashboard → Weather)
const forwardTransformed = await transformer.transform(
  dashboardData,
  "ui/dashboard#weather-widget",
  "services/weather#current",
  "forward"
);
console.log("Transformed to Weather format:", forwardTransformed);
console.log("Expected: { location: 'Tokyo' }");
console.log("Match:", JSON.stringify(forwardTransformed) === JSON.stringify({ location: "Tokyo" }));

console.log("\n--- Weather Service Response ---");
console.log("Weather returns:", weatherResponse);

// Reverse transform (Weather → Dashboard)
const reverseTransformed = await transformer.transform(
  weatherResponse,
  "services/weather#current",
  "ui/dashboard#weather-widget",
  "reverse"
);
console.log("Transformed to Dashboard format:", reverseTransformed);
console.log("Expected: { temp: 25.5, humid: 60, city: 'Tokyo' }");
console.log("Match:", JSON.stringify(reverseTransformed) === JSON.stringify({ temp: 25.5, humid: 60, city: "Tokyo" }));