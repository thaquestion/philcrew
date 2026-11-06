# Builds the phil.meshtc.com page from the Claude page source: swaps the Claude store for Firebase, keyed by the crew PIN.
import sys,json
src,dst,cfgf=sys.argv[1],sys.argv[2],sys.argv[3]
s=open(src).read(); fb=open(cfgf).read().strip()
def rep(a,b):
    global s
    assert s.count(a)==1,(a[:70],s.count(a)); s=s.replace(a,b)
s=s.replace('<meta name="claude:viewport-fit-sides" content="cover">\n','')
rep('This view is read-only. Ask TJ for edit access.','Saving was refused. Reopen the page and enter the PIN.')
SHIM=r'''/* ---------- Firebase store, keyed by the crew PIN ---------- */
const FIREBASE_CONFIG=__FBCFG__;
const FBV="https://www.gstatic.com/firebasejs/10.12.2/";
const SALT="philcrew-barncreek-2026";
function lsGet(k){try{return localStorage.getItem(k)}catch(e){return null}}
function lsSet(k,v){try{v==null?localStorage.removeItem(k):localStorage.setItem(k,v)}catch(e){}}
async function pinKey(pin){const enc=new TextEncoder();const base=await crypto.subtle.importKey("raw",enc.encode(pin),"PBKDF2",false,["deriveBits"]);const bits=await crypto.subtle.deriveBits({name:"PBKDF2",hash:"SHA-256",salt:enc.encode(SALT),iterations:250000},base,256);return[...new Uint8Array(bits)].map(b=>b.toString(16).padStart(2,"0")).join("")}
let F=null,FS=null;
async function fbInit(){if(FS)return;const A=await import(FBV+"firebase-app.js");F=await import(FBV+"firebase-firestore.js");const app=A.initializeApp(FIREBASE_CONFIG);try{FS=F.initializeFirestore(app,{localCache:F.persistentLocalCache({tabManager:F.persistentMultipleTabManager()})})}catch(e){FS=F.getFirestore(app)}}
const clean=b=>JSON.parse(JSON.stringify(b));
function makeDb(key){const ref=p=>F.doc(FS,"crews",key,...p.split("/"));const wrapDoc=d=>({id:d.id,exists:d.exists(),data:()=>d.data()||{}});
return{doc:p=>({set:b=>F.setDoc(ref(p),clean(b)),delete:()=>F.deleteDoc(ref(p)),onSnapshot:(f,err)=>F.onSnapshot(ref(p),d=>f(wrapDoc(d)),err)}),
collection:c=>{const parts=[];const q={orderBy:(k,d)=>{parts.push(F.orderBy(k,d||"asc"));return q},limit:n=>{parts.push(F.limit(n));return q},onSnapshot:(f,err)=>F.onSnapshot(F.query(F.collection(FS,"crews",key,c),...parts),s=>f({docs:s.docs.map(wrapDoc)}),err)};return q}}}
async function boardExists(key){const d=await F.getDoc(F.doc(FS,"crews",key,"race","config"));return d.exists()}
async function seedBoard(key){const r=await fetch("seed.json",{cache:"no-store"});const docs=await r.json();const b=F.writeBatch(FS);Object.entries(docs).forEach(([p,d])=>b.set(F.doc(FS,"crews",key,...p.split("/")),d));await b.commit()}
function pinGate(msg){return new Promise(res=>{let pending=null;
const draw=(m,setup)=>{$("#app").innerHTML='<div class="card"><div class="h">Crew PIN</div><div class="muted">'+(setup?'No board uses this PIN yet. Type it again to set up Phil\'s board with it. Share it only with the crew and Phil.':'Enter the PIN TJ gave you. This phone remembers it.')+'</div><input id="pinIn" type="password" inputmode="numeric" autocomplete="off" aria-label="PIN" style="font-size:22px"><button class="btn primary big" id="pinGo">'+(setup?'Set up the board':'Open the board')+'</button>'+(setup?'<button class="btn ghost" id="pinBack">Use a different PIN</button>':'')+'<div class="mini" id="pinMsg" style="color:var(--bad)">'+(m||"")+'</div></div>';
const go=async()=>{const pin=$("#pinIn").value.trim();if(!pin)return;if(pin.length<6){$("#pinMsg").textContent="Use at least 6 digits.";return}$("#pinMsg").style.color="var(--muted)";$("#pinMsg").textContent="Checking…";
try{await fbInit();if(setup){if(pin!==pending){draw("Those didn't match. Start again.",false);pending=null;return}const key=await pinKey(pin);$("#pinMsg").textContent="Loading Phil's plan…";await seedBoard(key);lsSet("crewKey",key);res(key);return}
const key=await pinKey(pin);if(await boardExists(key)){lsSet("crewKey",key);res(key)}else{pending=pin;draw("",true)}}catch(e){$("#pinMsg").style.color="var(--bad)";$("#pinMsg").textContent="Can't reach the board. Check signal and try again."}};
$("#pinGo").onclick=go;$("#pinIn").onkeydown=e=>{if(e.key==="Enter")go()};const bk=$("#pinBack");if(bk)bk.onclick=()=>{pending=null;draw("",false)};setTimeout(()=>{try{$("#pinIn").focus()}catch(e){}},50)};
draw(msg,false)})}
'''.replace("__FBCFG__",fb)
rep('/* ---------- boot ---------- */',SHIM+'/* ---------- boot ---------- */')
old_start='let db=null;try{db=window.claude&&await window.claude.use("db")}catch(e){}'
i=s.index(old_start); j=s.index('const done=k=>',i)
s=s[:i]+'''clearTimeout(to);let key=lsGet("crewKey");if(key){try{await fbInit()}catch(e){key=null}}if(!key)key=await pinGate();
const db=makeDb(key);S.db=db;
const to2=setTimeout(()=>{const n=$("#loadNote");if(n)n.textContent="Can't reach the crew board yet. Check signal; it keeps trying."},10000);
'''+s[j:]
s=s.replace('if(S.loaded.config&&S.loaded.menu&&S.loaded.laps)clearTimeout(to);','if(S.loaded.config&&S.loaded.menu&&S.loaded.laps)clearTimeout(to2);')
# a "Leave this board" link in Setup so a phone can switch PIN
rep('''h+='<div class="card"><div class="h">Runner view</div>''','''h+='<div class="card"><div class="h">This phone</div><div class="muted">Forget the PIN on this phone.</div><button class="btn ghost" data-act="forgetpin">Forget PIN</button></div>';
h+='<div class="card"><div class="h">Runner view</div>''')
rep('case"care":{','case"forgetpin":{lsSet("crewKey",null);location.reload();break}\ncase"care":{')
out='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="robots" content="noindex"></head><body>\n'+s+'\n</body></html>\n'
open(dst,'w').write(out); print("built",len(out))
