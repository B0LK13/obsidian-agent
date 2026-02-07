/**
 * Confidence Calibration - Task 4
 * Compute Brier score and ECE from live benchmark runs
 */

export interface ConfidenceCalibration {
  brierScore: number;
  ece: number; // Expected Calibration Error
  perTypeBrier: Record<string, number>;
  perTypeECE: Record<string, number>;
  calibrationCurve: { predicted: number; actual: number; count: number }[];
}

/**
 * Calculate Brier score (lower is better, 0 = perfect)
 * Brier = mean((predicted - actual)²)
 */
export function calculateBrierScore(predictions: { predicted: number; actual: number }[]): number {
  if (predictions.length === 0) return 1.0;
  
  const sumSquaredErrors = predictions.reduce((sum, p) => {
    return sum + Math.pow(p.predicted - p.actual, 2);
  }, 0);
  
  return sumSquaredErrors / predictions.length;
}

/**
 * Calculate Expected Calibration Error (ECE)
 * ECE measures calibration quality across probability bins
 */
export function calculateECE(
  predictions: { predicted: number; actual: number }[],
  numBins: number = 10
): number {
  if (predictions.length === 0) return 1.0;
  
  // Create bins [0-0.1, 0.1-0.2, ..., 0.9-1.0]
  const bins: { predicted: number[]; actual: number[] }[] = Array(numBins).fill(null).map(() => ({
    predicted: [],
    actual: []
  }));
  
  // Assign predictions to bins
  for (const p of predictions) {
    const binIndex = Math.min(Math.floor(p.predicted * numBins), numBins - 1);
    bins[binIndex].predicted.push(p.predicted);
    bins[binIndex].actual.push(p.actual);
  }
  
  // Calculate ECE
  let ece = 0;
  const totalSamples = predictions.length;
  
  for (const bin of bins) {
    if (bin.predicted.length === 0) continue;
    
    const avgPredicted = bin.predicted.reduce((sum, p) => sum + p, 0) / bin.predicted.length;
    const avgActual = bin.actual.reduce((sum, a) => sum + a, 0) / bin.actual.length;
    const binWeight = bin.predicted.length / totalSamples;
    
    ece += binWeight * Math.abs(avgPredicted - avgActual);
  }
  
  return ece;
}

/**
 * Calibrate confidence thresholds by query type
 */
export function calibrateByType(
  predictions: { type: string; predicted: number; actual: number }[]
): Record<string, { brierScore: number; ece: number; recommendedThreshold: number }> {
  const byType: Record<string, { predicted: number; actual: number }[]> = {};
  
  // Group by type
  for (const p of predictions) {
    if (!byType[p.type]) byType[p.type] = [];
    byType[p.type].push({ predicted: p.predicted, actual: p.actual });
  }
  
  // Calculate metrics per type
  const result: Record<string, { brierScore: number; ece: number; recommendedThreshold: number }> = {};
  
  for (const [type, preds] of Object.entries(byType)) {
    const brier = calculateBrierScore(preds);
    const ece = calculateECE(preds);
    
    // Recommend threshold based on calibration quality
    // If ECE is high, recommend higher confidence threshold
    const recommendedThreshold = ece > 0.15 ? 0.7 : ece > 0.10 ? 0.6 : 0.5;
    
    result[type] = {
      brierScore: brier,
      ece,
      recommendedThreshold
    };
  }
  
  return result;
}

/**
 * Generate calibration curve for visualization
 */
export function generateCalibrationCurve(
  predictions: { predicted: number; actual: number }[],
  numBins: number = 10
): { predicted: number; actual: number; count: number }[] {
  const bins: { predicted: number[]; actual: number[] }[] = Array(numBins).fill(null).map(() => ({
    predicted: [],
    actual: []
  }));
  
  for (const p of predictions) {
    const binIndex = Math.min(Math.floor(p.predicted * numBins), numBins - 1);
    bins[binIndex].predicted.push(p.predicted);
    bins[binIndex].actual.push(p.actual);
  }
  
  return bins.map((bin, idx) => {
    if (bin.predicted.length === 0) {
      return { predicted: (idx + 0.5) / numBins, actual: 0, count: 0 };
    }
    
    return {
      predicted: bin.predicted.reduce((sum, p) => sum + p, 0) / bin.predicted.length,
      actual: bin.actual.reduce((sum, a) => sum + a, 0) / bin.actual.length,
      count: bin.predicted.length
    };
  }).filter(point => point.count > 0);
}
