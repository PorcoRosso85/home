// Analyze Revenue Sensitivity Query
// Purpose: Analyze revenue sensitivity to changes in partner parameters
// Parameters: sensitivityFactors, variationPercentage
// Returns: Revenue impact analysis for different parameter changes

MATCH (p:Partner)-[c:CONTRIBUTED_TO]->(t:Transaction)
WHERE t.timestamp >= $startDate AND t.timestamp <= $endDate
OPTIONAL MATCH (p)-[:HAS_REWARD_STRUCTURE]->(rs:RewardStructure)
WITH p, rs,
     COUNT(t) AS baseTransactions,
     SUM(t.amount) AS baseRevenue,
     AVG(c.contributionScore) AS baseContribution,
     AVG(t.amount) AS baseAvgTransaction
WITH p, rs, baseTransactions, baseRevenue, baseContribution, baseAvgTransaction,
     COALESCE($variationPercentage, 10) AS variation  // Default 10% variation
// Scenario 1: Partner Contribution Score Changes
WITH p, rs, baseTransactions, baseRevenue, baseContribution, baseAvgTransaction, variation,
     baseRevenue * (1 + (variation/100.0)) AS revenueWithIncreasedContribution,
     baseRevenue * (1 - (variation/100.0)) AS revenueWithDecreasedContribution
// Scenario 2: Transaction Volume Changes
WITH p, rs, baseTransactions, baseRevenue, baseContribution, baseAvgTransaction, variation,
     revenueWithIncreasedContribution, revenueWithDecreasedContribution,
     (baseTransactions * (1 + variation/100.0)) * baseAvgTransaction AS revenueWithIncreasedVolume,
     (baseTransactions * (1 - variation/100.0)) * baseAvgTransaction AS revenueWithDecreasedVolume
// Scenario 3: Average Transaction Value Changes
WITH p, rs, baseTransactions, baseRevenue, baseContribution, variation,
     revenueWithIncreasedContribution, revenueWithDecreasedContribution,
     revenueWithIncreasedVolume, revenueWithDecreasedVolume,
     baseTransactions * (baseAvgTransaction * (1 + variation/100.0)) AS revenueWithIncreasedValue,
     baseTransactions * (baseAvgTransaction * (1 - variation/100.0)) AS revenueWithDecreasedValue
// Calculate reward cost impacts
WITH p, rs, baseTransactions, baseRevenue, variation,
     revenueWithIncreasedContribution, revenueWithDecreasedContribution,
     revenueWithIncreasedVolume, revenueWithDecreasedVolume,
     revenueWithIncreasedValue, revenueWithDecreasedValue,
     CASE rs.type
       WHEN 'percentage' THEN baseRevenue * rs.rate
       WHEN 'fixed' THEN baseTransactions * rs.fixedAmount
       ELSE baseRevenue * 0.05
     END AS baseRewardCost
WITH p, baseRevenue, variation, baseRewardCost,
     revenueWithIncreasedContribution, revenueWithDecreasedContribution,
     revenueWithIncreasedVolume, revenueWithDecreasedVolume,
     revenueWithIncreasedValue, revenueWithDecreasedValue,
     // Calculate net impact (revenue change - reward cost change)
     (revenueWithIncreasedContribution - baseRevenue) AS contributionUpImpact,
     (revenueWithDecreasedContribution - baseRevenue) AS contributionDownImpact,
     (revenueWithIncreasedVolume - baseRevenue) AS volumeUpImpact,
     (revenueWithDecreasedVolume - baseRevenue) AS volumeDownImpact,
     (revenueWithIncreasedValue - baseRevenue) AS valueUpImpact,
     (revenueWithDecreasedValue - baseRevenue) AS valueDownImpact
// Calculate sensitivity ratios
WITH p, baseRevenue, variation, baseRewardCost,
     contributionUpImpact, contributionDownImpact,
     volumeUpImpact, volumeDownImpact,
     valueUpImpact, valueDownImpact,
     // Sensitivity = (% change in revenue) / (% change in parameter)
     (contributionUpImpact / baseRevenue) / (variation / 100.0) AS contributionSensitivity,
     (volumeUpImpact / baseRevenue) / (variation / 100.0) AS volumeSensitivity,
     (valueUpImpact / baseRevenue) / (variation / 100.0) AS valueSensitivity
// Aggregate across all partners
WITH variation,
     SUM(baseRevenue) AS totalBaseRevenue,
     SUM(baseRewardCost) AS totalBaseRewardCost,
     SUM(contributionUpImpact) AS totalContributionUpImpact,
     SUM(contributionDownImpact) AS totalContributionDownImpact,
     SUM(volumeUpImpact) AS totalVolumeUpImpact,
     SUM(volumeDownImpact) AS totalVolumeDownImpact,
     SUM(valueUpImpact) AS totalValueUpImpact,
     SUM(valueDownImpact) AS totalValueDownImpact,
     AVG(contributionSensitivity) AS avgContributionSensitivity,
     AVG(volumeSensitivity) AS avgVolumeSensitivity,
     AVG(valueSensitivity) AS avgValueSensitivity
RETURN variation AS variationPercent,
       totalBaseRevenue AS baselineRevenue,
       totalBaseRewardCost AS baselineRewardCost,
       // Contribution sensitivity
       totalContributionUpImpact AS contributionIncreaseImpact,
       totalContributionDownImpact AS contributionDecreaseImpact,
       avgContributionSensitivity AS contributionSensitivityRatio,
       // Volume sensitivity
       totalVolumeUpImpact AS volumeIncreaseImpact,
       totalVolumeDownImpact AS volumeDecreaseImpact,
       avgVolumeSensitivity AS volumeSensitivityRatio,
       // Value sensitivity
       totalValueUpImpact AS valueIncreaseImpact,
       totalValueDownImpact AS valueDecreaseImpact,
       avgValueSensitivity AS valueSensitivityRatio,
       // Risk assessment
       CASE 
         WHEN abs(avgVolumeSensitivity) > abs(avgValueSensitivity) AND abs(avgVolumeSensitivity) > abs(avgContributionSensitivity) THEN 'VOLUME_SENSITIVE'
         WHEN abs(avgValueSensitivity) > abs(avgContributionSensitivity) THEN 'VALUE_SENSITIVE'
         ELSE 'CONTRIBUTION_SENSITIVE'
       END AS primaryRiskFactor,
       CASE 
         WHEN avgVolumeSensitivity > 2 OR avgValueSensitivity > 2 OR avgContributionSensitivity > 2 THEN 'HIGH_SENSITIVITY'
         WHEN avgVolumeSensitivity > 1 OR avgValueSensitivity > 1 OR avgContributionSensitivity > 1 THEN 'MODERATE_SENSITIVITY'
         ELSE 'LOW_SENSITIVITY'
       END AS overallSensitivityLevel