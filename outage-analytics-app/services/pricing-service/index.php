<?php
/**
 * Pricing Service (PHP) — Energy pricing/tariff calculations
 * Adds PHP to polyglot mix (like AstroShop's Quote service)
 * Calculates energy rates based on region, time-of-use, and demand
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$method = $_SERVER['REQUEST_METHOD'];
$query = [];
parse_str(parse_url($_SERVER['REQUEST_URI'], PHP_URL_QUERY) ?? '', $query);

// Rate classes and tariff data
$rateClasses = [
    'R-1' => ['name' => 'Residential Standard', 'baseRate' => 0.098, 'peakRate' => 0.142, 'offPeakRate' => 0.067, 'demandCharge' => 0, 'fixedCharge' => 12.50],
    'R-2' => ['name' => 'Residential Time-of-Use', 'baseRate' => 0.085, 'peakRate' => 0.168, 'offPeakRate' => 0.054, 'demandCharge' => 0, 'fixedCharge' => 14.00],
    'C-1' => ['name' => 'Commercial Small', 'baseRate' => 0.082, 'peakRate' => 0.125, 'offPeakRate' => 0.058, 'demandCharge' => 8.50, 'fixedCharge' => 25.00],
    'C-2' => ['name' => 'Commercial Large', 'baseRate' => 0.071, 'peakRate' => 0.108, 'offPeakRate' => 0.048, 'demandCharge' => 12.75, 'fixedCharge' => 45.00],
    'I-1' => ['name' => 'Industrial', 'baseRate' => 0.058, 'peakRate' => 0.092, 'offPeakRate' => 0.038, 'demandCharge' => 18.50, 'fixedCharge' => 85.00],
];

$regions = [
    'Chicago-Metro' => ['multiplier' => 1.0, 'fuel_adjustment' => 0.012, 'transmission' => 0.028, 'distribution' => 0.035],
    'Baltimore-Metro' => ['multiplier' => 1.08, 'fuel_adjustment' => 0.015, 'transmission' => 0.031, 'distribution' => 0.038],
    'Philadelphia-Metro' => ['multiplier' => 1.12, 'fuel_adjustment' => 0.014, 'transmission' => 0.029, 'distribution' => 0.036],
    'DC-Metro' => ['multiplier' => 1.15, 'fuel_adjustment' => 0.016, 'transmission' => 0.033, 'distribution' => 0.040],
    'Atlantic-Coast' => ['multiplier' => 1.05, 'fuel_adjustment' => 0.013, 'transmission' => 0.027, 'distribution' => 0.034],
    'Delaware-Valley' => ['multiplier' => 1.03, 'fuel_adjustment' => 0.011, 'transmission' => 0.026, 'distribution' => 0.033],
];

function isPeakHour() {
    $hour = (int)date('G');
    return $hour >= 14 && $hour <= 19; // 2 PM - 7 PM
}

function isSuperPeak() {
    $hour = (int)date('G');
    return $hour >= 16 && $hour <= 18; // 4 PM - 6 PM
}

function calculateRate($rateClass, $region, $kwh = 1000) {
    global $rateClasses, $regions;
    $rc = $rateClasses[$rateClass] ?? $rateClasses['R-1'];
    $rg = $regions[$region] ?? $regions['Chicago-Metro'];
    
    $isPeak = isPeakHour();
    $isSuperPeak = isSuperPeak();
    $baseRate = $isPeak ? $rc['peakRate'] : $rc['offPeakRate'];
    if ($isSuperPeak) $baseRate *= 1.15;
    
    $effectiveRate = $baseRate * $rg['multiplier'];
    $totalRate = $effectiveRate + $rg['fuel_adjustment'] + $rg['transmission'] + $rg['distribution'];
    
    $energyCharge = $kwh * $totalRate;
    $demandCharge = $rc['demandCharge'] * ($kwh / 730); // Approximate demand kW
    $totalBill = $energyCharge + $demandCharge + $rc['fixedCharge'];
    
    return [
        'rateClass' => $rateClass,
        'rateClassName' => $rc['name'],
        'region' => $region,
        'kwhUsage' => $kwh,
        'isPeakPeriod' => $isPeak,
        'isSuperPeak' => $isSuperPeak,
        'baseRatePerKwh' => round($baseRate, 4),
        'regionalMultiplier' => $rg['multiplier'],
        'effectiveRatePerKwh' => round($effectiveRate, 4),
        'fuelAdjustment' => $rg['fuel_adjustment'],
        'transmissionCharge' => $rg['transmission'],
        'distributionCharge' => $rg['distribution'],
        'totalRatePerKwh' => round($totalRate, 4),
        'energyCharge' => round($energyCharge, 2),
        'demandCharge' => round($demandCharge, 2),
        'fixedCharge' => $rc['fixedCharge'],
        'totalEstimate' => round($totalBill, 2),
        'calculatedAt' => date('c'),
    ];
}

// Routing
switch (true) {
    // Current pricing for all rate classes
    case $path === '/api/pricing/current' && $method === 'GET':
        $region = $query['region'] ?? null;
        $result = [
            'timestamp' => date('c'),
            'isPeakPeriod' => isPeakHour(),
            'isSuperPeak' => isSuperPeak(),
            'currentHour' => (int)date('G'),
            'rates' => [],
        ];
        foreach ($rateClasses as $classId => $rc) {
            $rg = $region ? ($regions[$region] ?? $regions['Chicago-Metro']) : $regions['Chicago-Metro'];
            $baseRate = isPeakHour() ? $rc['peakRate'] : $rc['offPeakRate'];
            if (isSuperPeak()) $baseRate *= 1.15;
            $result['rates'][] = [
                'rateClass' => $classId,
                'name' => $rc['name'],
                'currentRate' => round($baseRate * $rg['multiplier'], 4),
                'peakRate' => round($rc['peakRate'] * $rg['multiplier'], 4),
                'offPeakRate' => round($rc['offPeakRate'] * $rg['multiplier'], 4),
                'fixedCharge' => $rc['fixedCharge'],
                'demandCharge' => $rc['demandCharge'],
            ];
        }
        echo json_encode($result);
        break;

    // Calculate price for specific usage
    case $path === '/api/pricing/calculate' && $method === 'GET':
        $rateClass = $query['rateClass'] ?? 'R-1';
        $region = $query['region'] ?? 'Chicago-Metro';
        $kwh = (float)($query['kwh'] ?? 1000);
        echo json_encode(calculateRate($rateClass, $region, $kwh));
        break;

    // Rate classes listing
    case $path === '/api/pricing/rates' && $method === 'GET':
        $result = [];
        foreach ($rateClasses as $id => $rc) {
            $rc['id'] = $id;
            $result[] = $rc;
        }
        echo json_encode(['rateClasses' => $result]);
        break;

    // Regional pricing multipliers
    case $path === '/api/pricing/regions' && $method === 'GET':
        echo json_encode(['regions' => $regions]);
        break;

    // Outage cost impact estimate
    case $path === '/api/pricing/outage-impact' && $method === 'GET':
        $customers = (int)($query['customers'] ?? 100);
        $hours = (float)($query['hours'] ?? 2);
        $avgKwhPerHour = 1.2; // average residential consumption per hour
        $avgRate = 0.12;
        $lostRevenue = $customers * $avgKwhPerHour * $hours * $avgRate;
        $penaltyCost = $customers > 500 ? $customers * 2.50 : 0;
        $restorationCost = $customers * 15.00;
        echo json_encode([
            'affectedCustomers' => $customers,
            'outageDurationHours' => $hours,
            'lostRevenueEstimate' => round($lostRevenue, 2),
            'regulatoryPenalty' => round($penaltyCost, 2),
            'restorationCostEstimate' => round($restorationCost, 2),
            'totalImpactEstimate' => round($lostRevenue + $penaltyCost + $restorationCost, 2),
            'calculatedAt' => date('c'),
        ]);
        break;

    // Health check
    case $path === '/api/pricing/health' && $method === 'GET':
        echo json_encode([
            'status' => 'Healthy',
            'service' => 'pricing-service',
            'language' => 'PHP',
            'timestamp' => date('c'),
        ]);
        break;

    default:
        http_response_code(404);
        echo json_encode(['error' => 'Not found', 'path' => $path]);
        break;
}
