"""
Test suite for the Test Completeness Report module
"""
import pytest
import json
import csv
import os
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

from test_completeness_report import TestCompletenessAnalyzer


class TestTestCompletenessAnalyzer:
    """Test the TestCompletenessAnalyzer functionality"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance without database"""
        return TestCompletenessAnalyzer()
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for file outputs"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_category_completeness_analysis(self, analyzer):
        """Test category-wise completeness analysis"""
        analysis = analyzer.analyze_category_completeness()
        
        # Verify structure
        assert isinstance(analysis, dict)
        assert 'authentication' in analysis
        assert 'session' in analysis
        assert 'access_control' in analysis
        
        # Verify authentication category
        auth = analysis['authentication']
        assert auth['total_requirements'] == 6
        assert auth['implemented_count'] == 4
        assert auth['coverage_percentage'] == pytest.approx(66.67, rel=0.01)
        assert auth['status'] == 'fair'
        assert auth['priority_score'] == 20
        assert len(auth['missing_requirements']) == 2
        
        # Verify missing requirements structure
        missing_req = auth['missing_requirements'][0]
        assert 'id' in missing_req
        assert 'level' in missing_req
        assert 'description' in missing_req
    
    def test_project_coverage_analysis(self, analyzer):
        """Test project-level coverage analysis"""
        coverage = analyzer.analyze_project_coverage()
        
        # Verify overall metrics
        assert coverage['overall']['total_requirements'] == 12
        assert coverage['overall']['implemented_requirements'] == 7
        assert coverage['overall']['coverage_percentage'] == pytest.approx(58.33, rel=0.01)
        assert coverage['overall']['grade'] == 'D'
        
        # Verify coverage by standard
        assert 'ASVS' in coverage['by_standard']
        asvs = coverage['by_standard']['ASVS']
        assert asvs['total'] == 12
        assert asvs['implemented'] == 7
        assert asvs['percentage'] == pytest.approx(58.33, rel=0.01)
        
        # Verify coverage by level
        assert 'level_1' in coverage['by_level']
        assert 'level_2' in coverage['by_level']
        level1 = coverage['by_level']['level_1']
        assert level1['total'] == 8
        assert level1['implemented'] == 5
        assert level1['percentage'] == 62.5
        
        # Verify status breakdown
        assert coverage['by_status']['completed'] == 5
        assert coverage['by_status']['not_implemented'] == 5
        
        # Verify risk assessment
        risk = coverage['risk_assessment']
        assert risk['level'] == 'high'
        assert risk['score'] == 85
        assert 'Critical gaps' in risk['description']
    
    def test_gap_identification_with_priority(self, analyzer):
        """Test gap identification and priority scoring"""
        gaps = analyzer.identify_gaps_with_priority()
        
        assert isinstance(gaps, list)
        assert len(gaps) >= 3
        
        # Verify gap structure
        gap = gaps[0]
        assert 'id' in gap
        assert 'standard' in gap
        assert 'section' in gap
        assert 'level' in gap
        assert 'category' in gap
        assert 'description' in gap
        assert 'priority_score' in gap
        assert 'risk_level' in gap
        assert 'remediation_effort' in gap
        assert 'dependencies' in gap
        
        # Verify priority sorting (descending)
        priorities = [g['priority_score'] for g in gaps]
        assert priorities == sorted(priorities, reverse=True)
        
        # Verify high priority gaps
        high_priority_gaps = [g for g in gaps if g['risk_level'] == 'high']
        assert len(high_priority_gaps) >= 3
        
        # Verify Level 1 gaps have high priority
        level1_gaps = [g for g in gaps if g['level'] == 1]
        for gap in level1_gaps:
            assert gap['priority_score'] >= 70
    
    def test_trend_analysis(self, analyzer):
        """Test trend analysis over time"""
        trends = analyzer.analyze_trends(days=30)
        
        # Verify period information
        assert trends['period']['days'] == 30
        assert 'start' in trends['period']
        assert 'end' in trends['period']
        
        # Verify daily coverage data
        daily = trends['daily_coverage']
        assert len(daily) == 30
        assert all('date' in d and 'coverage' in d for d in daily)
        
        # Verify coverage improves over time
        first_coverage = daily[0]['coverage']
        last_coverage = daily[-1]['coverage']
        assert last_coverage > first_coverage
        
        # Verify weekly averages
        weekly = trends['weekly_averages']
        assert len(weekly) >= 4  # At least 4 weeks in 30 days
        assert all('week_start' in w and 'average_coverage' in w for w in weekly)
        
        # Verify improvement velocity
        assert trends['improvement_velocity'] > 0
        
        # Verify projected completion
        assert trends['projected_completion'] is not None
    
    def test_json_export(self, analyzer, temp_dir):
        """Test JSON export functionality"""
        filepath = os.path.join(temp_dir, 'report.json')
        analyzer.export_json(filepath)
        
        assert os.path.exists(filepath)
        
        # Load and verify JSON
        with open(filepath, 'r') as f:
            report = json.load(f)
        
        assert 'metadata' in report
        assert 'category_analysis' in report
        assert 'project_coverage' in report
        assert 'gap_analysis' in report
        assert 'trend_analysis' in report
        assert 'summary' in report
        
        # Verify metadata
        assert report['metadata']['version'] == '1.0.0'
        assert report['metadata']['analyzer'] == 'TestCompletenessAnalyzer'
    
    def test_csv_export(self, analyzer, temp_dir):
        """Test CSV export functionality"""
        filepath = os.path.join(temp_dir, 'report.csv')
        analyzer.export_csv(filepath)
        
        # Check that multiple CSV files are created
        category_file = filepath.replace('.csv', '_categories.csv')
        gaps_file = filepath.replace('.csv', '_gaps.csv')
        
        assert os.path.exists(category_file)
        assert os.path.exists(gaps_file)
        
        # Verify category CSV
        with open(category_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) >= 3  # At least 3 categories
        assert 'Category' in rows[0]
        assert 'Total Requirements' in rows[0]
        assert 'Coverage %' in rows[0]
        
        # Verify gaps CSV
        with open(gaps_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) >= 3  # At least 3 gaps
        assert 'ID' in rows[0]
        assert 'Priority Score' in rows[0]
        assert 'Risk Level' in rows[0]
    
    def test_html_export(self, analyzer, temp_dir):
        """Test HTML export functionality"""
        filepath = os.path.join(temp_dir, 'report.html')
        analyzer.export_html(filepath)
        
        assert os.path.exists(filepath)
        
        # Read and verify HTML content
        with open(filepath, 'r') as f:
            html_content = f.read()
        
        # Check for key elements
        assert '<title>Test Completeness Report' in html_content
        assert 'Overall Project Coverage' in html_content
        assert 'Coverage by Category' in html_content
        assert 'Top Priority Gaps' in html_content
        assert 'Risk Assessment' in html_content
        
        # Check for data presence
        assert '58.3%' in html_content or '58.33%' in html_content  # Overall coverage
        assert 'grade-D' in html_content  # Grade D
        assert 'high-priority' in html_content  # High priority gaps
    
    def test_coverage_grading(self, analyzer):
        """Test coverage percentage to grade conversion"""
        assert analyzer._calculate_grade(95) == 'A'
        assert analyzer._calculate_grade(85) == 'B'
        assert analyzer._calculate_grade(75) == 'C'
        assert analyzer._calculate_grade(65) == 'D'
        assert analyzer._calculate_grade(55) == 'F'
        assert analyzer._calculate_grade(45) == 'F'
    
    def test_coverage_status_determination(self, analyzer):
        """Test coverage status determination"""
        assert analyzer._get_coverage_status(95) == 'excellent'
        assert analyzer._get_coverage_status(80) == 'good'
        assert analyzer._get_coverage_status(60) == 'fair'
        assert analyzer._get_coverage_status(30) == 'poor'
        assert analyzer._get_coverage_status(15) == 'critical'
    
    def test_risk_assessment_logic(self, analyzer):
        """Test risk assessment based on metrics"""
        # High risk scenario
        metrics_high_risk = {
            'overall': {'coverage_percentage': 45},
            'by_level': {'level_1': {'percentage': 55}}
        }
        risk = analyzer._assess_risk(metrics_high_risk)
        assert risk['level'] == 'high'
        assert risk['score'] == 85
        
        # Medium risk scenario
        metrics_medium_risk = {
            'overall': {'coverage_percentage': 70},
            'by_level': {'level_1': {'percentage': 75}}
        }
        risk = analyzer._assess_risk(metrics_medium_risk)
        assert risk['level'] == 'medium'
        assert risk['score'] == 50
        
        # Low risk scenario
        metrics_low_risk = {
            'overall': {'coverage_percentage': 85},
            'by_level': {'level_1': {'percentage': 90}}
        }
        risk = analyzer._assess_risk(metrics_low_risk)
        assert risk['level'] == 'low'
        assert risk['score'] == 20
    
    def test_complete_report_generation(self, analyzer):
        """Test complete report generation"""
        report = analyzer._generate_complete_report()
        
        # Verify all sections present
        assert 'metadata' in report
        assert 'category_analysis' in report
        assert 'project_coverage' in report
        assert 'gap_analysis' in report
        assert 'trend_analysis' in report
        assert 'summary' in report
        
        # Verify summary
        summary = report['summary']
        assert summary['overall_health'] == 'D'
        assert summary['critical_gaps'] >= 3
        assert summary['total_gaps'] >= 3
        assert len(summary['recommendations']) >= 1
    
    def test_recommendations_generation(self, analyzer):
        """Test that appropriate recommendations are generated"""
        coverage = analyzer.analyze_project_coverage()
        gaps = analyzer.identify_gaps_with_priority()
        
        recommendations = analyzer._generate_recommendations(coverage, gaps)
        
        assert isinstance(recommendations, list)
        assert len(recommendations) >= 1
        
        # Should recommend urgent action for low coverage
        assert any('Urgently' in r for r in recommendations)
        
        # Should mention Level 1 requirements
        assert any('Level 1' in r for r in recommendations)
    
    def test_priority_score_calculation(self, analyzer):
        """Test priority score calculation for gaps"""
        # Level 1 requirement in critical category
        gap_high = {'level': 1, 'category': 'authentication', 'standard': 'ASVS'}
        score = analyzer._calculate_gap_priority(gap_high)
        assert score >= 70  # High priority
        
        # Level 2 requirement in normal category
        gap_medium = {'level': 2, 'category': 'logging', 'standard': 'ASVS'}
        score = analyzer._calculate_gap_priority(gap_medium)
        assert 30 <= score <= 50  # Medium priority
        
        # Level 3 requirement
        gap_low = {'level': 3, 'category': 'other', 'standard': 'Other'}
        score = analyzer._calculate_gap_priority(gap_low)
        assert score <= 30  # Low priority
    
    def test_velocity_calculation(self, analyzer):
        """Test improvement velocity calculation"""
        velocity = analyzer._calculate_velocity(30)
        
        # Should be positive for improving coverage
        assert velocity > 0
        
        # Should be reasonable (not too high)
        assert velocity < 5.0  # Less than 5% per day
    
    def test_projected_completion(self, analyzer):
        """Test completion date projection"""
        completion = analyzer._project_completion(30)
        
        if completion:
            # Should be a valid date string
            completion_date = datetime.strptime(completion, '%Y-%m-%d')
            
            # Should be in the future
            assert completion_date > datetime.now()
            
            # Should be reasonable (not too far)
            assert completion_date < datetime.now() + timedelta(days=365)


class TestIntegrationScenarios:
    """Integration tests with mock database scenarios"""
    
    def test_high_coverage_scenario(self):
        """Test analyzer with high coverage scenario"""
        analyzer = TestCompletenessAnalyzer()
        
        # Override mock to simulate high coverage
        original_mock = analyzer._mock_project_coverage
        
        def high_coverage_mock():
            data = original_mock()
            data['overall']['coverage_percentage'] = 92.5
            data['overall']['implemented_requirements'] = 11
            data['overall']['grade'] = 'A'
            data['risk_assessment'] = {
                'level': 'low',
                'score': 15,
                'description': 'Excellent coverage, maintain current standards'
            }
            return data
        
        analyzer._mock_project_coverage = high_coverage_mock
        
        # Generate report
        coverage = analyzer.analyze_project_coverage()
        assert coverage['overall']['grade'] == 'A'
        assert coverage['risk_assessment']['level'] == 'low'
    
    def test_critical_coverage_scenario(self):
        """Test analyzer with critical coverage scenario"""
        analyzer = TestCompletenessAnalyzer()
        
        # Override mock to simulate critical coverage
        original_mock = analyzer._mock_project_coverage
        
        def critical_coverage_mock():
            data = original_mock()
            data['overall']['coverage_percentage'] = 15.0
            data['overall']['implemented_requirements'] = 2
            data['overall']['grade'] = 'F'
            data['by_level']['level_1']['percentage'] = 12.5
            data['risk_assessment'] = {
                'level': 'high',
                'score': 95,
                'description': 'Critical security gaps require immediate attention'
            }
            return data
        
        analyzer._mock_project_coverage = critical_coverage_mock
        
        # Generate report and verify recommendations
        coverage = analyzer.analyze_project_coverage()
        gaps = analyzer.identify_gaps_with_priority()
        recommendations = analyzer._generate_recommendations(coverage, gaps)
        
        assert coverage['overall']['grade'] == 'F'
        assert any('Urgently' in r for r in recommendations)
        assert len(recommendations) >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])