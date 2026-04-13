/**
 * Browser Traffic Generator — Creates real Dynatrace RUM sessions
 *
 * Uses Playwright (headless Chromium) to simulate realistic user personas.
 * Each persona follows role-based journeys with drill-downs, table clicks,
 * filters, map interactions, cross-links, and search — generating rich RUM data.
 * Sessions are limited to MAX_SESSION_MINUTES (default: 10).
 *
 * Environment variables:
 *   APP_MODE             - "utility", "retail", or "generic" (default: utility)
 *   APP_URL              - Base URL of the application
 *   CONCURRENT_USERS     - Number of parallel browser sessions (default: 3)
 *   SESSION_INTERVAL     - Seconds between new sessions per slot (default: 60)
 *   MAX_SESSION_MINUTES  - Max duration per session in minutes (default: 10)
 */

const { chromium } = require('playwright');

const APP_MODE = process.env.APP_MODE || 'utility';
const APP_URL = process.env.APP_URL || 'https://utility.vptesttools.my';
const CONCURRENT_USERS = parseInt(process.env.CONCURRENT_USERS || '3', 10);
const SESSION_INTERVAL = parseInt(process.env.SESSION_INTERVAL || '60', 10) * 1000;
const MAX_SESSION_MS = parseInt(process.env.MAX_SESSION_MINUTES || '10', 10) * 60 * 1000;

const PERSONAS = [
  { username: 'operator_jones', role: 'operator', journeys: ['storm_response','outage_triage','routine_monitoring'], weight: 3 },
  { username: 'engineer_chen', role: 'engineer', journeys: ['scada_investigation','grid_inspection','reliability_review'], weight: 2 },
  { username: 'manager_smith', role: 'manager', journeys: ['executive_overview','reliability_review','storm_response'], weight: 2 },
  { username: 'analyst_garcia', role: 'analyst', journeys: ['reliability_review','meter_anomaly','pricing_analysis'], weight: 2 },
  { username: 'dispatcher_lee', role: 'dispatcher', journeys: ['crew_dispatch','outage_triage','storm_response'], weight: 3 },
  { username: 'supervisor_patel', role: 'supervisor', journeys: ['executive_overview','crew_dispatch','customer_callback'], weight: 2 },
  { username: 'technician_wong', role: 'technician', journeys: ['scada_investigation','grid_inspection','outage_triage'], weight: 2 },
  { username: 'director_johnson', role: 'director', journeys: ['executive_overview','reliability_review','audit_review'], weight: 1 },
  { username: 'operator_brown', role: 'operator', journeys: ['routine_monitoring','outage_triage','weather_check'], weight: 2 },
  { username: 'engineer_martinez', role: 'engineer', journeys: ['grid_inspection','scada_investigation','alert_correlation'], weight: 2 },
  { username: 'analyst_taylor', role: 'analyst', journeys: ['meter_anomaly','pricing_analysis','reliability_review'], weight: 1 },
  { username: 'dispatcher_harris', role: 'dispatcher', journeys: ['crew_dispatch','storm_response','customer_callback'], weight: 2 },
  { username: 'technician_clark', role: 'technician', journeys: ['scada_investigation','outage_triage','workorder_management'], weight: 1 },
  { username: 'manager_lewis', role: 'manager', journeys: ['executive_overview','audit_review','customer_callback'], weight: 1 },
  { username: 'operator_robinson', role: 'operator', journeys: ['routine_monitoring','weather_check','outage_triage'], weight: 1 },
];

const JOURNEYS = {
  storm_response: [
    {t:'nav',s:'overview'},{t:'w',a:3,b:6},{t:'scroll'},{t:'map'},{t:'w',a:2,b:4},
    {t:'nav',s:'weather'},{t:'w',a:3,b:8},{t:'scroll'},{t:'nav',s:'outages'},{t:'w',a:2,b:5},
    {t:'row'},{t:'w',a:4,b:8},{t:'nav',s:'crew'},{t:'w',a:2,b:5},{t:'row'},{t:'w',a:3,b:6},
    {t:'nav',s:'notifications'},{t:'w',a:2,b:4},{t:'nav',s:'alertcorrelation'},{t:'w',a:3,b:6},{t:'scroll'},
  ],
  outage_triage: [
    {t:'nav',s:'outages'},{t:'w',a:2,b:5},{t:'fsel',v:'Critical'},{t:'w',a:2,b:4},
    {t:'row'},{t:'w',a:5,b:10},{t:'back'},{t:'w',a:2,b:4},{t:'fsel',v:'Active'},{t:'w',a:2,b:4},
    {t:'row'},{t:'w',a:4,b:8},{t:'nav',s:'crew'},{t:'w',a:2,b:5},{t:'row'},{t:'w',a:3,b:6},{t:'scroll'},
  ],
  routine_monitoring: [
    {t:'nav',s:'overview'},{t:'w',a:5,b:10},{t:'scroll'},{t:'kpi'},{t:'w',a:3,b:6},
    {t:'nav',s:'scada'},{t:'w',a:3,b:6},{t:'row'},{t:'w',a:3,b:6},{t:'nav',s:'health'},{t:'w',a:3,b:5},
    {t:'nav',s:'metering'},{t:'w',a:2,b:5},{t:'row'},{t:'w',a:3,b:6},{t:'scroll'},
    {t:'nav',s:'livefeed'},{t:'w',a:5,b:10},{t:'nav',s:'overview'},{t:'w',a:2,b:4},
  ],
  scada_investigation: [
    {t:'nav',s:'scada'},{t:'w',a:3,b:6},{t:'row'},{t:'w',a:5,b:10},{t:'back'},{t:'w',a:2,b:4},
    {t:'nav',s:'alertcorrelation'},{t:'w',a:3,b:6},{t:'scroll'},
    {t:'nav',s:'scada'},{t:'w',a:2,b:5},{t:'row'},{t:'w',a:4,b:8},
  ],
  grid_inspection: [
    {t:'nav',s:'grid'},{t:'w',a:3,b:6},{t:'click',sel:'.topology-node'},{t:'w',a:2,b:4},
    {t:'scroll'},{t:'nav',s:'scada'},{t:'w',a:3,b:6},{t:'row'},{t:'w',a:3,b:6},
    {t:'nav',s:'reliability'},{t:'w',a:3,b:6},{t:'scroll'},
  ],
  reliability_review: [
    {t:'nav',s:'reliability'},{t:'w',a:3,b:8},{t:'scroll'},{t:'nav',s:'overview'},{t:'w',a:2,b:4},
    {t:'kpi'},{t:'w',a:3,b:6},{t:'nav',s:'outages'},{t:'w',a:2,b:5},{t:'row'},{t:'w',a:4,b:8},
    {t:'nav',s:'forecast'},{t:'w',a:3,b:6},{t:'scroll'},{t:'nav',s:'reliability'},{t:'w',a:2,b:4},
  ],
  crew_dispatch: [
    {t:'nav',s:'crew'},{t:'w',a:2,b:5},{t:'row'},{t:'w',a:4,b:8},{t:'back'},{t:'w',a:2,b:4},
    {t:'nav',s:'outages'},{t:'w',a:2,b:4},{t:'row'},{t:'w',a:4,b:8},
    {t:'nav',s:'crew'},{t:'w',a:2,b:5},{t:'scroll'},{t:'nav',s:'notifications'},{t:'w',a:2,b:4},
  ],
  customer_callback: [
    {t:'search',q:'customer'},{t:'w',a:2,b:4},{t:'nav',s:'customers'},{t:'w',a:2,b:5},
    {t:'row'},{t:'w',a:5,b:10},{t:'back'},{t:'w',a:2,b:4},
    {t:'nav',s:'outages'},{t:'w',a:2,b:5},{t:'row'},{t:'w',a:3,b:6},
    {t:'nav',s:'notifications'},{t:'w',a:2,b:4},{t:'scroll'},
  ],
  executive_overview: [
    {t:'nav',s:'overview'},{t:'w',a:5,b:10},{t:'scroll'},{t:'map'},{t:'w',a:3,b:6},
    {t:'mapstate'},{t:'w',a:5,b:10},{t:'scroll'},{t:'row'},{t:'w',a:3,b:6},
    {t:'nav',s:'reliability'},{t:'w',a:3,b:6},{t:'nav',s:'forecast'},{t:'w',a:3,b:6},{t:'scroll'},
    {t:'nav',s:'health'},{t:'w',a:2,b:4},{t:'nav',s:'overview'},{t:'w',a:3,b:6},
  ],
  weather_check: [
    {t:'nav',s:'weather'},{t:'w',a:3,b:8},{t:'scroll'},{t:'nav',s:'overview'},{t:'w',a:2,b:4},
    {t:'map'},{t:'w',a:3,b:6},{t:'nav',s:'forecast'},{t:'w',a:3,b:6},{t:'scroll'},
    {t:'nav',s:'alertcorrelation'},{t:'w',a:2,b:5},{t:'scroll'},
  ],
  meter_anomaly: [
    {t:'nav',s:'metering'},{t:'w',a:3,b:6},{t:'row'},{t:'w',a:5,b:10},{t:'back'},{t:'w',a:2,b:4},
    {t:'nav',s:'metering'},{t:'w',a:2,b:4},{t:'scroll'},
    {t:'nav',s:'customers'},{t:'w',a:2,b:5},{t:'row'},{t:'w',a:4,b:8},
  ],
  pricing_analysis: [
    {t:'nav',s:'pricing'},{t:'w',a:3,b:6},{t:'scroll'},
    {t:'click',sel:'button:has-text("Calculate")'},{t:'w',a:3,b:6},
    {t:'nav',s:'customers'},{t:'w',a:2,b:5},{t:'row'},{t:'w',a:4,b:8},
  ],
  workorder_management: [
    {t:'nav',s:'workorders'},{t:'w',a:2,b:5},{t:'row'},{t:'w',a:5,b:10},
    {t:'back'},{t:'w',a:2,b:4},{t:'nav',s:'workorders'},{t:'w',a:2,b:4},
    {t:'nav',s:'auditlog'},{t:'w',a:2,b:5},{t:'scroll'},
  ],
  audit_review: [
    {t:'nav',s:'auditlog'},{t:'w',a:3,b:6},{t:'fsel',v:'critical'},{t:'w',a:2,b:4},
    {t:'scroll'},{t:'nav',s:'health'},{t:'w',a:2,b:4},
    {t:'nav',s:'overview'},{t:'w',a:3,b:6},
  ],
  alert_correlation: [
    {t:'nav',s:'alertcorrelation'},{t:'w',a:3,b:6},{t:'scroll'},
    {t:'nav',s:'scada'},{t:'w',a:2,b:5},{t:'row'},{t:'w',a:4,b:8},
    {t:'nav',s:'weather'},{t:'w',a:2,b:5},{t:'scroll'},
    {t:'nav',s:'outages'},{t:'w',a:2,b:4},{t:'row'},{t:'w',a:3,b:6},
  ],
};

const STATE_CODES = ['IL','PA','NJ','MD','OH','NY','MA','GA','FL','TX','TN','NC','MI','MN','MO'];
const USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.4 Safari/605.1.15',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
];
const VIEWPORTS = [
  {width:1920,height:1080},{width:1440,height:900},{width:1366,height:768},{width:2560,height:1440},{width:1280,height:720},
];

function pick(a){return a[Math.floor(Math.random()*a.length)]}
function sleep(ms){return new Promise(r=>setTimeout(r,ms))}
function rSleep(a,b){return sleep((a+Math.random()*(b-a))*1000)}
function timeLeft(s){return(Date.now()-s)<MAX_SESSION_MS}
function pickPersona(){const e=[];PERSONAS.forEach(p=>{for(let i=0;i<p.weight;i++)e.push(p)});return pick(e)}

async function exec(page,a,slot,start){
  if(!timeLeft(start))return false;
  try{switch(a.t){
    case'nav':{
      const b=page.locator(`.nav button[data-section="${a.s}"]`);
      if(await b.isVisible().catch(()=>false))await b.click();
      else await page.evaluate(s=>{window.location.hash=s},a.s);
      await page.waitForLoadState('networkidle').catch(()=>{});
      console.log(`[${slot}] nav:#${a.s}`);break;
    }
    case'w':await rSleep(a.a,a.b);break;
    case'scroll':
      await page.evaluate(()=>window.scrollBy(0,Math.random()*400+100));
      await rSleep(0.5,1.5);
      await page.evaluate(()=>window.scrollTo(0,0));break;
    case'row':{
      const rows=page.locator('tr.clickable-row');
      const c=await rows.count().catch(()=>0);
      if(c>0){const i=Math.floor(Math.random()*Math.min(c,5));
        await rows.nth(i).click().catch(()=>{});
        await page.waitForLoadState('networkidle').catch(()=>{});
        console.log(`[${slot}] row:${i}`);}break;
    }
    case'click':{
      const el=page.locator(a.sel);
      if(await el.first().isVisible().catch(()=>false)){
        await el.first().click().catch(()=>{});
        await page.waitForLoadState('networkidle').catch(()=>{});}break;
    }
    case'back':{
      const btn=page.locator('.detail-actions .btn, .breadcrumb a').first();
      if(await btn.isVisible().catch(()=>false)){
        await btn.click().catch(()=>{});
        await page.waitForLoadState('networkidle').catch(()=>{});
        console.log(`[${slot}] back`);}break;
    }
    case'fsel':{
      const sels=page.locator('.filter-controls select, .filter-bar select');
      const c=await sels.count().catch(()=>0);
      if(c>0){await sels.first().selectOption(a.v).catch(()=>{});
        await rSleep(0.5,1);console.log(`[${slot}] filter:${a.v}`);}break;
    }
    case'kpi':{
      const k=page.locator('.kpi[data-drill]');
      const c=await k.count().catch(()=>0);
      if(c>0){await k.nth(Math.floor(Math.random()*c)).click().catch(()=>{});
        await page.waitForLoadState('networkidle').catch(()=>{});
        console.log(`[${slot}] kpi`);}break;
    }
    case'map':{
      const m=page.locator('#leaflet-map');
      if(await m.isVisible().catch(()=>false)){
        const box=await m.boundingBox();
        if(box){await page.mouse.move(box.x+box.width/2,box.y+box.height/2);
          await page.mouse.wheel(0,-200);await rSleep(1,2);await page.mouse.wheel(0,200);}
        console.log(`[${slot}] mapZoom`);}break;
    }
    case'mapstate':{
      const sc=pick(STATE_CODES);
      await page.evaluate(c=>{if(typeof drillToState==='function')drillToState(c)},sc).catch(()=>{});
      await page.waitForLoadState('networkidle').catch(()=>{});
      console.log(`[${slot}] state:${sc}`);break;
    }
    case'search':{
      const si=page.locator('#search-input');
      if(await si.isVisible().catch(()=>false)){
        await si.fill(a.q);await rSleep(1,2);
        const ri=page.locator('.search-item');
        if(await ri.first().isVisible().catch(()=>false))await ri.first().click().catch(()=>{});
        console.log(`[${slot}] search:"${a.q}"`);}break;
    }
  }}catch(e){}
  return timeLeft(start);
}

async function runUtilitySession(browser,slotId){
  const p=pickPersona(),start=Date.now();
  // Generate a unique IP per session to help server-side RUM create distinct sessions
  const sessionIp=`10.${50+Math.floor(Math.random()*200)}.${Math.floor(Math.random()*256)}.${1+Math.floor(Math.random()*254)}`;
  const ctx=await browser.newContext({
    ignoreHTTPSErrors:true,
    viewport:pick(VIEWPORTS),
    userAgent:pick(USER_AGENTS),
    extraHTTPHeaders:{'X-Forwarded-For':sessionIp,'X-Real-IP':sessionIp}
  });
  const page=await ctx.newPage();
  let actions=0;
  try{
    console.log(`[${slotId}] START ${p.username}(${p.role})`);
    await page.goto(APP_URL,{waitUntil:'networkidle',timeout:30000});
    await rSleep(2,4);
    const lo=page.locator('#login-overlay');
    if(await lo.isVisible().catch(()=>false)){
      const sel=page.locator('#login-user-select');
      if(await sel.isVisible().catch(()=>false))await sel.selectOption(p.username);
      await page.fill('#login-username',p.username);
      await page.fill('#login-password','utility2026');
      await rSleep(0.5,1);await page.click('#login-submit');await rSleep(2,4);
    }
    // Wait for Dynatrace RUM agent to load, then identify user
    await page.waitForFunction(()=>typeof dtrum!=='undefined'&&typeof dtrum.identifyUser==='function',{timeout:10000}).catch(()=>{});
    await page.evaluate(u=>{if(typeof dtrum!=='undefined'&&dtrum.identifyUser)dtrum.identifyUser(u)},p.username).catch(()=>{});
    await page.evaluate(r=>{if(typeof dtrum!=='undefined'&&dtrum.sendSessionProperties)dtrum.sendSessionProperties(null,null,{role:r})},p.role).catch(()=>{});
    const nj=2+Math.floor(Math.random()*2);
    for(let j=0;j<nj&&timeLeft(start);j++){
      const jn=pick(p.journeys),journey=JOURNEYS[jn];
      if(!journey)continue;
      console.log(`[${slotId}] journey:${jn}(${journey.length}steps)`);
      for(const a of journey){
        if(!timeLeft(start))break;
        const ok=await exec(page,a,slotId,start);
        if(a.t!=='w')actions++;
        if(!ok)break;
      }
      if(timeLeft(start))await rSleep(3,8);
    }
    const lb=page.locator('.user-menu');
    if(await lb.first().isVisible().catch(()=>false))await lb.first().click().catch(()=>{});
    // End Dynatrace RUM session explicitly before closing context
    await page.evaluate(()=>{if(typeof dtrum!=='undefined'&&dtrum.endSession)dtrum.endSession()}).catch(()=>{});
    await rSleep(1,2);
    console.log(`[${slotId}] END ${p.username}: ${actions}actions ${Math.round((Date.now()-start)/1000)}s`);
  }catch(e){console.error(`[${slotId}] ERR:`,e.message);}
  finally{await ctx.close();}
}

async function sessionLoop(browser,slotId){
  while(true){
    await runUtilitySession(browser,slotId);
    const j=SESSION_INTERVAL*(0.5+Math.random());
    console.log(`[${slotId}] next in ${Math.round(j/1000)}s`);
    await sleep(j);
  }
}

async function main(){
  console.log(`=== Browser Traffic Generator ===`);
  console.log(`Mode:${APP_MODE} URL:${APP_URL} Users:${CONCURRENT_USERS} MaxSession:${MAX_SESSION_MS/60000}min`);
  console.log(`Personas:${PERSONAS.length} Journeys:${Object.keys(JOURNEYS).length}`);
  const browser=await chromium.launch({headless:true,args:['--no-sandbox','--disable-setuid-sandbox','--disable-dev-shm-usage','--disable-gpu']});
  console.log(`Browser:Chromium ${browser.version()}`);
  const slots=[];
  for(let i=0;i<CONCURRENT_USERS;i++){
    slots.push(sleep(i*5000).then(()=>sessionLoop(browser,i+1)));
  }
  await Promise.all(slots);
}

main().catch(e=>{console.error('Fatal:',e);process.exit(1)});
