/**
 * Analytics Domain Types
 * 
 * Pure domain types for analytics and charting functionality.
 * No dependencies on infrastructure or presentation layers.
 */

/**
 * Numeric value for chart data points
 */
export type ChartValue = number;

/**
 * Color value in hex format
 */
export type HexColor = string;

/**
 * Chart data point label
 */
export type ChartLabel = string;

/**
 * Index for chart data points or segments
 */
export type ChartIndex = number;

/**
 * Basic data point for charts
 */
export interface DataPoint {
  /** Human-readable label */
  label: ChartLabel;
  /** Numeric value */
  value: ChartValue;
  /** Color representation */
  color: HexColor;
}

/**
 * Chart configuration for donut/pie charts
 */
export interface DonutChartConfig {
  /** Center X coordinate */
  centerX: number;
  /** Center Y coordinate */
  centerY: number;
  /** Outer radius */
  radius: number;
  /** Inner radius (for donut effect) */
  innerRadius: number;
}

/**
 * SVG path data for chart segments
 */
export interface ChartSegment {
  /** SVG path string */
  path: string;
  /** Associated data point */
  dataPoint: DataPoint;
  /** Segment index */
  index: ChartIndex;
}

/**
 * Chart interaction state
 */
export interface ChartInteractionState {
  /** Currently hovered segment index */
  hoveredIndex: ChartIndex | null;
  /** Currently selected segment index */
  selectedIndex: ChartIndex | null;
}

/**
 * Chart rendering dimensions
 */
export interface ChartDimensions {
  /** Chart width */
  width: number;
  /** Chart height */
  height: number;
  /** SVG viewBox */
  viewBox: string;
}

/**
 * Analytics data aggregation
 */
export interface DataAggregation {
  /** Total sum of all values */
  total: ChartValue;
  /** Average value */
  average: ChartValue;
  /** Maximum value */
  maximum: ChartValue;
  /** Minimum value */
  minimum: ChartValue;
  /** Number of data points */
  count: number;
}

/**
 * Chart theme configuration
 */
export interface ChartTheme {
  /** Default stroke width */
  strokeWidth: number;
  /** Default stroke color */
  strokeColor: HexColor;
  /** Default background color */
  backgroundColor?: HexColor;
  /** Font family for text elements */
  fontFamily: string;
  /** Default font size */
  fontSize: number;
}

/**
 * Chart legend configuration
 */
export interface ChartLegend {
  /** Whether to show legend */
  show: boolean;
  /** Legend position relative to chart */
  position: 'top' | 'bottom' | 'left' | 'right';
  /** Spacing between legend items */
  itemSpacing: number;
  /** Legend marker size */
  markerSize: number;
}

/**
 * Complete chart configuration
 */
export interface ChartConfiguration {
  /** Chart dimensions */
  dimensions: ChartDimensions;
  /** Donut chart specific config */
  donut: DonutChartConfig;
  /** Theme settings */
  theme: ChartTheme;
  /** Legend settings */
  legend: ChartLegend;
}

/**
 * Chart data validation result
 */
export interface ChartDataValidation {
  /** Whether data is valid */
  isValid: boolean;
  /** Validation error messages */
  errors: string[];
  /** Warnings (non-blocking) */
  warnings: string[];
}