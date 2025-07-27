#!/usr/bin/env python3
"""
Example usage of the Test Completeness Report module

This script demonstrates how to use the TestCompletenessAnalyzer to generate
comprehensive test coverage reports in various formats.
"""
import os
import tempfile
from test_completeness_report import TestCompletenessAnalyzer


def main():
    """Demonstrate test completeness report generation"""
    print("Test Completeness Report - Example Usage")
    print("=" * 50)
    
    # Create analyzer instance (using mock data without database)
    analyzer = TestCompletenessAnalyzer()
    
    # 1. Category-wise Completeness Analysis
    print("\n1. Category-wise Completeness Analysis:")
    print("-" * 40)
    
    category_analysis = analyzer.analyze_category_completeness()
    for category, data in category_analysis.items():
        print(f"\n{category.upper()}:")
        print(f"  Total Requirements: {data['total_requirements']}")
        print(f"  Implemented: {data['implemented_count']}")
        print(f"  Coverage: {data['coverage_percentage']:.1f}%")
        print(f"  Status: {data['status']}")
        print(f"  Priority Score: {data['priority_score']}")
        if data['missing_requirements']:
            print(f"  Missing ({len(data['missing_requirements'])}):")
            for req in data['missing_requirements'][:2]:  # Show first 2
                print(f"    - {req['id']}: {req['description']}")
    
    # 2. Project-level Coverage
    print("\n\n2. Project-level Coverage Analysis:")
    print("-" * 40)
    
    project_coverage = analyzer.analyze_project_coverage()
    overall = project_coverage['overall']
    print(f"Overall Coverage: {overall['coverage_percentage']:.1f}% (Grade: {overall['grade']})")
    print(f"Total Requirements: {overall['total_requirements']}")
    print(f"Implemented: {overall['implemented_requirements']}")
    
    print("\nBy Status:")
    for status, count in project_coverage['by_status'].items():
        print(f"  {status}: {count}")
    
    print("\nBy Level:")
    for level, data in project_coverage['by_level'].items():
        print(f"  {level}: {data['percentage']:.1f}% ({data['implemented']}/{data['total']})")
    
    print("\nRisk Assessment:")
    risk = project_coverage['risk_assessment']
    print(f"  Level: {risk['level'].upper()}")
    print(f"  Score: {risk['score']}/100")
    print(f"  Description: {risk['description']}")
    
    # 3. Gap Identification with Priority
    print("\n\n3. Top Priority Gaps:")
    print("-" * 40)
    
    gaps = analyzer.identify_gaps_with_priority()
    print(f"Total Gaps Identified: {len(gaps)}")
    print("\nTop 5 Priority Gaps:")
    
    for i, gap in enumerate(gaps[:5], 1):
        print(f"\n{i}. {gap['id']} ({gap['standard']} - Level {gap['level']})")
        print(f"   Category: {gap['category']}")
        print(f"   Description: {gap['description']}")
        print(f"   Priority Score: {gap['priority_score']}")
        print(f"   Risk Level: {gap['risk_level']}")
        print(f"   Remediation Effort: {gap['remediation_effort']}")
    
    # 4. Trend Analysis
    print("\n\n4. Trend Analysis (Last 30 Days):")
    print("-" * 40)
    
    trends = analyzer.analyze_trends(days=30)
    print(f"Period: {trends['period']['start'][:10]} to {trends['period']['end'][:10]}")
    print(f"Improvement Velocity: {trends['improvement_velocity']:.2f}% per day")
    
    if trends['projected_completion']:
        print(f"Projected 100% Completion: {trends['projected_completion']}")
    else:
        print("Projected Completion: Unable to estimate")
    
    print("\nWeekly Averages:")
    for week in trends['weekly_averages'][:2]:  # Show first 2 weeks
        print(f"  Week of {week['week_start']}: {week['average_coverage']:.1f}%")
    
    # 5. Generate Reports
    print("\n\n5. Generating Reports:")
    print("-" * 40)
    
    # Create temporary directory for reports
    with tempfile.TemporaryDirectory() as temp_dir:
        # Generate all report formats
        json_path = os.path.join(temp_dir, "completeness_report.json")
        csv_path = os.path.join(temp_dir, "completeness_report.csv")
        html_path = os.path.join(temp_dir, "completeness_report.html")
        
        print(f"Generating JSON report...")
        analyzer.export_json(json_path)
        print(f"  ✓ JSON report saved to: {json_path}")
        
        print(f"\nGenerating CSV reports...")
        analyzer.export_csv(csv_path)
        print(f"  ✓ Category CSV saved to: {csv_path.replace('.csv', '_categories.csv')}")
        print(f"  ✓ Gaps CSV saved to: {csv_path.replace('.csv', '_gaps.csv')}")
        
        print(f"\nGenerating HTML report...")
        analyzer.export_html(html_path)
        print(f"  ✓ HTML report saved to: {html_path}")
        
        # Show file sizes
        print("\nReport File Sizes:")
        for path in [json_path, 
                    csv_path.replace('.csv', '_categories.csv'),
                    csv_path.replace('.csv', '_gaps.csv'),
                    html_path]:
            if os.path.exists(path):
                size = os.path.getsize(path)
                print(f"  {os.path.basename(path)}: {size:,} bytes")
    
    # 6. Summary and Recommendations
    print("\n\n6. Summary and Recommendations:")
    print("-" * 40)
    
    report = analyzer._generate_complete_report()
    summary = report['summary']
    
    print(f"Overall Health: Grade {summary['overall_health']}")
    print(f"Critical Gaps: {summary['critical_gaps']}")
    print(f"Total Gaps: {summary['total_gaps']}")
    
    print("\nRecommendations:")
    for i, rec in enumerate(summary['recommendations'], 1):
        print(f"  {i}. {rec}")
    
    print("\n" + "=" * 50)
    print("Example completed successfully!")
    print("\nNote: This example uses mock data. In production, connect to a real KuzuDB")
    print("database with actual test coverage data for accurate analysis.")


if __name__ == "__main__":
    main()