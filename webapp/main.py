# ============================================================
# BACKEND - Bai giua ky IoT (thay the Blynk bang web tu xay)
# Kien truc: ESP32 (Slave) --HTTPS--> server nay (Cloud, deploy tren Render)
#            --> phuc vu Dashboard (Control and Display) cho trinh duyet qua Internet.
#
# API:
#   POST /api/data     ESP32 day so lieu cam bien len, nhan lai lenh dieu khien
#                       dang cho (tra trong CUNG 1 request, khoi phai goi rieng).
#   POST /api/control   Trinh duyet gui lenh dieu khien thu cong.
#   GET  /api/data      Trinh duyet doc so lieu moi nhat de ve Dashboard.
#   GET  /             Trang Dashboard (HTML tinh, JS tu poll /api/data moi giay).
# ============================================================
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI(title="Bai giua ky IoT - Dashboard")

# Trang thai duy nhat, luu thang trong bo nho (khong can database cho quy mo bai nay).
trang_thai = {
    "nhietDo": None,
    "doAm": None,
    "anhSang": None,
    "quatDangBat": False,
    "pwmDen": 0,
    "cheDoThuCong": False,
    "quatThuCong": False,
    "capNhatLuc": None,  # ISO timestamp lan cuoi ESP32 gui du lieu len
}

NGUONG_OFFLINE_GIAY = 10  # khong nhan duoc goi moi trong 10s -> coi la mat ket noi


@app.post("/api/data")
async def esp32_day_du_lieu(request: Request):
    """ESP32 goi moi 2 giay: day so lieu cam bien, nhan lai lenh dieu khien dang cho."""
    goi = await request.json()
    trang_thai["nhietDo"] = goi.get("nhietDo")
    trang_thai["doAm"] = goi.get("doAm")
    trang_thai["anhSang"] = goi.get("anhSang")
    trang_thai["quatDangBat"] = bool(goi.get("quatDangBat", False))
    trang_thai["pwmDen"] = goi.get("pwmDen", 0)
    trang_thai["capNhatLuc"] = datetime.now(timezone.utc).isoformat()

    # Tra ve dung lenh dieu khien hien tai - ESP32 ap dung ngay, khong can goi them.
    return {
        "cheDoThuCong": trang_thai["cheDoThuCong"],
        "quatThuCong": trang_thai["quatThuCong"],
    }


@app.post("/api/control")
async def trinh_duyet_dieu_khien(request: Request):
    """Trinh duyet goi khi bam nut tren Dashboard."""
    goi = await request.json()
    if "cheDoThuCong" in goi:
        trang_thai["cheDoThuCong"] = bool(goi["cheDoThuCong"])
    if "quatThuCong" in goi:
        trang_thai["quatThuCong"] = bool(goi["quatThuCong"])
    return {"ok": True}


@app.get("/api/data")
async def trinh_duyet_lay_du_lieu():
    """Trinh duyet goi moi giay de ve lai Dashboard."""
    online = False
    if trang_thai["capNhatLuc"] is not None:
        lan_cuoi = datetime.fromisoformat(trang_thai["capNhatLuc"])
        online = (datetime.now(timezone.utc) - lan_cuoi).total_seconds() < NGUONG_OFFLINE_GIAY
    return {**trang_thai, "online": online}


@app.get("/", response_class=HTMLResponse)
async def trang_chu():
    return TRANG_HTML


TRANG_HTML = r"""<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Giám sát nông trại · Bài giữa kỳ</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
--mono:ui-monospace,'SF Mono','Cascadia Mono','Roboto Mono',Menlo,Consolas,monospace;
--ink:#080B12;--panel:#0E1420;--rail:#1B2434;--mist:#78879F;--paper:#E9EEF6;
--signal:#FF7A45;--ice:#45D0FF;--live:#4ADE80;
--signal-t:#FF7A45;--ice-t:#45D0FF;--live-t:#4ADE80;
--track:#141C29;--btn:#0B1119;--btn-on:#111926;
--scan:rgba(255,255,255,.015);--sky1:#0C121E;--sky2:#080B12;
--badge1:#17202F;--badge2:#0A1017;--halo:rgba(255,255,255,.045);
--gl:7px;--limop:.7;--flash:#FFFFFF}
:root[data-theme="light"]{
--ink:#EEF2F8;--panel:#FFFFFF;--rail:#DCE3EE;--mist:#66738A;--paper:#0D1622;
--signal:#F05A22;--ice:#12A0D8;--live:#16A34A;
--signal-t:#B23F13;--ice-t:#06688F;--live-t:#15803D;
--track:#E5EAF2;--btn:#F7F9FC;--btn-on:#FFFFFF;
--scan:rgba(15,23,42,.022);--sky1:#FFFFFF;--sky2:#E9EEF6;
--badge1:#FFFFFF;--badge2:#EDF1F8;--halo:rgba(15,23,42,.06);
--gl:3px;--limop:.9;--flash:var(--cd)}
@media(prefers-color-scheme:light){
:root:not([data-theme="dark"]){
--ink:#EEF2F8;--panel:#FFFFFF;--rail:#DCE3EE;--mist:#66738A;--paper:#0D1622;
--signal:#F05A22;--ice:#12A0D8;--live:#16A34A;
--signal-t:#B23F13;--ice-t:#06688F;--live-t:#15803D;
--track:#E5EAF2;--btn:#F7F9FC;--btn-on:#FFFFFF;
--scan:rgba(15,23,42,.022);--sky1:#FFFFFF;--sky2:#E9EEF6;
--badge1:#FFFFFF;--badge2:#EDF1F8;--halo:rgba(15,23,42,.06);
--gl:3px;--limop:.9;--flash:var(--cd)}}
body{font-family:var(--mono);color:var(--paper);min-height:100vh;padding:22px 18px 30px;
font-variant-numeric:tabular-nums;-webkit-font-smoothing:antialiased;
background:
 repeating-linear-gradient(0deg,var(--scan) 0 1px,transparent 1px 3px),
 linear-gradient(180deg,var(--sky1) 0%,var(--sky2) 60%);
background-color:var(--ink);transition:background-color .35s,color .35s}
.shell{max-width:760px;margin:0 auto}
.rail{display:flex;align-items:center;gap:14px}
header.rail{padding-bottom:16px;border-bottom:1px solid var(--rail);justify-content:space-between}
.brand{display:flex;align-items:center;gap:14px;flex:1;min-width:0}
.meta{display:flex;align-items:center;gap:12px;flex:0 0 auto}
.ueh{width:46px;height:46px;flex:0 0 auto;border-radius:14px;display:grid;place-items:center;
 background:linear-gradient(150deg,var(--badge1),var(--badge2));border:1px solid rgba(240,90,34,.38);
 font-size:12.5px;font-weight:700;letter-spacing:.09em}
.ueh span{background:linear-gradient(135deg,var(--signal),var(--ice));
 -webkit-background-clip:text;background-clip:text;color:transparent}
.title{flex:1;min-width:0}
h1{font-size:15px;font-weight:700;letter-spacing:.13em}
.title p{font-size:11px;color:var(--mist);letter-spacing:.04em;margin-top:4px}
.stat{display:flex;align-items:center;gap:7px;font-size:10.5px;letter-spacing:.13em;
 padding:7px 11px;border:1px solid var(--rail);border-radius:99px;color:var(--live-t);white-space:nowrap}
.stat i{width:6px;height:6px;border-radius:50%;background:currentColor;animation:beat 2.4s infinite}
.stat.off{color:var(--signal-t)}
.stat.off i{animation:none}
.tog{display:grid;place-items:center;width:34px;height:34px;flex:0 0 auto;cursor:pointer;
 background:var(--btn);border:1px solid var(--rail);border-radius:11px;color:var(--mist);
 transition:color .25s,border-color .25s,transform .13s,background .25s}
.tog:hover{color:var(--paper);border-color:var(--mist);transform:translateY(-1px)}
.tog .i-moon{display:none}
:root[data-theme="light"] .tog .i-sun{display:none}
:root[data-theme="light"] .tog .i-moon{display:block}
@media(prefers-color-scheme:light){
 :root:not([data-theme="dark"]) .tog .i-sun{display:none}
 :root:not([data-theme="dark"]) .tog .i-moon{display:block}}
.gauges{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:18px 0 14px}
.gauge{position:relative;overflow:hidden;background:var(--panel);border:1px solid var(--rail);transition:background-color .35s,border-color .35s;
 border-radius:22px;padding:20px 14px 18px;text-align:center}
.gauge::before{content:'';position:absolute;top:0;left:18%;right:18%;height:1px;
 background:linear-gradient(90deg,transparent,var(--c),transparent);opacity:.6}
.g-temp{--c:var(--signal);--cd:var(--signal-t)} .g-hum{--c:var(--ice);--cd:var(--ice-t)} .g-light{--c:#F5C518;--cd:#B08900}
.dial{position:relative;width:150px;height:150px;margin:0 auto}
.dial svg{width:100%;height:100%;display:block}
.tick{fill:none;stroke:var(--rail);stroke-width:1.5;stroke-dasharray:1.5 7.4;opacity:.85}
.track{fill:none;stroke:var(--track);stroke-width:8;stroke-linecap:round}
.arc{fill:none;stroke:var(--c);stroke-width:8;stroke-linecap:round;
 filter:drop-shadow(0 0 var(--gl) var(--c));transition:stroke-dasharray .7s cubic-bezier(.2,.8,.3,1)}
.spin{transform:rotate(135deg);transform-origin:75px 75px}
.read{position:absolute;inset:0;display:grid;place-content:center;gap:1px}
.read b{font-size:28px;font-weight:700;letter-spacing:-.03em;line-height:1;color:var(--paper)}
.read u{text-decoration:none;font-size:10px;color:var(--mist);letter-spacing:.14em;margin-top:5px}
.read b.hit{animation:hit .8s ease-out}
@keyframes hit{0%{color:var(--flash);text-shadow:0 0 18px var(--c)}100%{color:var(--paper);text-shadow:none}}
.gauge h2{margin-top:6px;font-size:11px;font-weight:700;letter-spacing:.2em;color:var(--cd)}
.gauge p{margin-top:5px;font-size:10px;color:var(--mist);letter-spacing:.07em}
.lim{position:absolute;bottom:14px;left:0;right:0;display:flex;justify-content:center;gap:50px;
 font-size:9px;color:var(--mist);opacity:var(--limop);letter-spacing:.08em;pointer-events:none}
.panel2{transition:background-color .35s,border-color .35s;background:var(--panel);border:1px solid var(--rail);border-radius:22px;padding:18px 18px 16px;margin-bottom:14px}
.panel-top{display:flex;align-items:baseline;justify-content:space-between;gap:12px;flex-wrap:wrap}
.panel-top h2{font-size:11px;font-weight:700;letter-spacing:.2em;color:var(--mist)}
.now{display:flex;align-items:center;gap:9px;font-size:13px;letter-spacing:.1em}
.now i{width:11px;height:11px;border-radius:50%;background:var(--now,#64748B);
 box-shadow:0 0 0 4px var(--halo),0 0 16px var(--now,#64748B);transition:.3s}
.now em{font-style:normal;font-size:10.5px;color:var(--mist);letter-spacing:.08em}
.btns{display:grid;grid-template-columns:repeat(2,1fr);gap:9px;margin-top:15px}
.btns.four{grid-template-columns:repeat(2,1fr)}
.b{--c:#4B5563;font:inherit;font-size:10.5px;letter-spacing:.1em;color:var(--paper);cursor:pointer;
 background:var(--btn);border:1px solid var(--rail);border-radius:13px;padding:13px 4px 12px;
 display:grid;justify-items:center;gap:8px;
 transition:transform .13s,border-color .25s,box-shadow .25s,background .25s}
.b i{width:9px;height:9px;border-radius:50%;background:var(--c);opacity:.55;transition:.25s}
.b:hover{transform:translateY(-2px);border-color:var(--c)}
.b:hover i{opacity:1}
.b:active{transform:translateY(0)}
.b.on{border-color:var(--c);background:var(--btn-on);box-shadow:0 0 0 1px var(--c),0 12px 26px -16px var(--c)}
.b.on i{opacity:1;box-shadow:0 0 12px var(--c)}
.b-auto{--c:#60A5FA} .b-manual{--c:#F59E0B} .b-on{--c:#34D399} .b-off{--c:#64748B}
.hint{font-size:10px;color:var(--mist);letter-spacing:.05em;margin-top:10px}
footer.rail{margin-top:14px;padding-top:14px;border-top:1px solid var(--rail);
 justify-content:space-between;font-size:10px;color:var(--mist);letter-spacing:.07em;flex-wrap:wrap}
@keyframes beat{0%{box-shadow:0 0 0 0 currentColor}70%{box-shadow:0 0 0 6px transparent}100%{box-shadow:0 0 0 0 transparent}}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
.rise{animation:rise .6s cubic-bezier(.2,.75,.3,1) both}
@media(max-width:640px){.gauges{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style></head><body>
<div class="shell">
 <header class="rail rise">
  <div class="brand">
   <div class="ueh"><span>UEH</span></div>
   <div class="title">
    <h1>GIÁM SÁT NÔNG TRẠI</h1>
    <p>ESP32 (Slave) → Cloud → Dashboard · qua Internet</p>
   </div>
  </div>
  <div class="meta">
   <span class="stat" id="stat"><i></i>ĐANG CHẠY</span>
   <button class="tog" id="tog" type="button" aria-label="Đổi nền sáng tối" title="Đổi nền sáng / tối">
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
     <g class="i-sun"><circle cx="12" cy="12" r="4.1"/><path d="M12 2.5v2.1M12 19.4v2.1M2.5 12h2.1M19.4 12h2.1M5.3 5.3l1.5 1.5M17.2 17.2l1.5 1.5M18.7 5.3l-1.5 1.5M6.8 17.2l-1.5 1.5"/></g>
     <path class="i-moon" d="M20 14.1A8.2 8.2 0 0 1 9.9 4 8.4 8.4 0 1 0 20 14.1z"/>
    </svg>
   </button>
  </div>
 </header>
 <section class="gauges">
  <article class="gauge g-temp rise" style="animation-delay:.07s">
   <div class="dial">
    <svg viewBox="0 0 150 150" aria-hidden="true">
     <circle class="tick spin" cx="75" cy="75" r="64"/>
     <circle class="track spin" cx="75" cy="75" r="53" stroke-dasharray="249.7 333"/>
     <circle class="arc spin" id="aT" cx="75" cy="75" r="53" stroke-dasharray="0 333"/>
    </svg>
    <div class="read"><b id="vT">--.-</b><u>&deg;C</u></div>
    <div class="lim"><span>0</span><span>50</span></div>
   </div>
   <h2>NHIỆT ĐỘ</h2>
  </article>
  <article class="gauge g-hum rise" style="animation-delay:.14s">
   <div class="dial">
    <svg viewBox="0 0 150 150" aria-hidden="true">
     <circle class="tick spin" cx="75" cy="75" r="64"/>
     <circle class="track spin" cx="75" cy="75" r="53" stroke-dasharray="249.7 333"/>
     <circle class="arc spin" id="aH" cx="75" cy="75" r="53" stroke-dasharray="0 333"/>
    </svg>
    <div class="read"><b id="vH">--.-</b><u>%</u></div>
    <div class="lim"><span>0</span><span>100</span></div>
   </div>
   <h2>ĐỘ ẨM</h2>
  </article>
  <article class="gauge g-light rise" style="animation-delay:.21s">
   <div class="dial">
    <svg viewBox="0 0 150 150" aria-hidden="true">
     <circle class="tick spin" cx="75" cy="75" r="64"/>
     <circle class="track spin" cx="75" cy="75" r="53" stroke-dasharray="249.7 333"/>
     <circle class="arc spin" id="aA" cx="75" cy="75" r="53" stroke-dasharray="0 333"/>
    </svg>
    <div class="read"><b id="vA">----</b><u>RAW</u></div>
    <div class="lim"><span>0</span><span>4095</span></div>
   </div>
   <h2>ÁNH SÁNG</h2>
  </article>
 </section>

 <section class="panel2 rise" style="animation-delay:.28s">
  <div class="panel-top">
   <h2>QUẠT & ĐÈN</h2>
   <div class="now" id="now"><i></i><span id="nowName">TẮT</span><em id="nowPwm">PWM --</em></div>
  </div>
  <div class="btns">
   <button class="b b-auto" id="bAuto" data-mode="auto"><i></i>TỰ ĐỘNG</button>
   <button class="b b-manual" id="bManual" data-mode="manual"><i></i>THỦ CÔNG</button>
  </div>
  <div class="btns">
   <button class="b b-on" id="bOn"><i></i>BẬT QUẠT</button>
   <button class="b b-off" id="bOff"><i></i>TẮT QUẠT</button>
  </div>
  <p class="hint">2 nút BẬT/TẮT QUẠT chỉ có tác dụng khi đang ở chế độ THỦ CÔNG. Ở chế độ TỰ ĐỘNG, quạt tự bật khi nhiệt độ &gt; 32&deg;C hoặc độ ẩm &gt; 80%.</p>
 </section>

 <footer class="rail rise" style="animation-delay:.35s">
  <span id="capnhat">Chưa nhận dữ liệu</span>
  <span>Dashboard tự làm mới mỗi giây</span>
 </footer>
</div>
<script>
try{var _t=localStorage.getItem('nen');if(_t)document.documentElement.setAttribute('data-theme',_t)}catch(e){}
</script>
<script>
var ARC=249.7,FULL=333,C={};
function el(i){return C[i]||(C[i]=document.getElementById(i))}
function arc(id,v,max){el(id).style.strokeDasharray=(Math.max(0,Math.min(1,v/max))*ARC).toFixed(1)+' '+FULL}
function num(id,v,digits){var e=el(id),t=v.toFixed(digits);if(e.textContent!==t){e.textContent=t;
 e.classList.remove('hit');void e.offsetWidth;e.classList.add('hit')}}

function paint(d){
 if(d.nhietDo!==null&&d.nhietDo!==undefined){num('vT',d.nhietDo,1);arc('aT',d.nhietDo,50)}
 if(d.doAm!==null&&d.doAm!==undefined){num('vH',d.doAm,1);arc('aH',d.doAm,100)}
 if(d.anhSang!==null&&d.anhSang!==undefined){num('vA',d.anhSang,0);arc('aA',d.anhSang,4095)}

 el('nowName').textContent=d.quatDangBat?'ĐANG BẬT':'TẮT';
 el('nowPwm').textContent='PWM '+d.pwmDen;
 el('now').style.setProperty('--now',d.quatDangBat?'#34D399':'#64748B');

 el('bAuto').classList.toggle('on',!d.cheDoThuCong);
 el('bManual').classList.toggle('on',!!d.cheDoThuCong);
 el('bOn').classList.toggle('on',!!d.cheDoThuCong&&!!d.quatThuCong);
 el('bOff').classList.toggle('on',!!d.cheDoThuCong&&!d.quatThuCong);

 var s=el('stat');
 if(d.online){s.classList.remove('off');s.lastChild.textContent='ĐANG CHẠY'}
 else{s.classList.add('off');s.lastChild.textContent='MẤT KẾT NỐI'}

 if(d.capNhatLuc){
  var t=new Date(d.capNhatLuc);
  el('capnhat').textContent='Cập nhật lúc '+t.toLocaleTimeString('vi-VN');
 }
}
function offline(){var s=el('stat');s.classList.add('off');s.lastChild.textContent='MẤT KẾT NỐI'}
function poll(){fetch('/api/data',{cache:'no-store'}).then(function(r){return r.json()}).then(paint).catch(offline)}
function guiLenh(body){
 fetch('/api/control',{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify(body),cache:'no-store'}).then(poll).catch(offline)
}
el('bAuto').addEventListener('click',function(){guiLenh({cheDoThuCong:false})});
el('bManual').addEventListener('click',function(){guiLenh({cheDoThuCong:true})});
el('bOn').addEventListener('click',function(){guiLenh({quatThuCong:true})});
el('bOff').addEventListener('click',function(){guiLenh({quatThuCong:false})});

var goc=document.documentElement;
el('tog').addEventListener('click',function(){
 var cur=goc.getAttribute('data-theme');
 if(!cur)cur=window.matchMedia('(prefers-color-scheme: light)').matches?'light':'dark';
 var moi=cur==='light'?'dark':'light';
 goc.setAttribute('data-theme',moi);
 try{localStorage.setItem('nen',moi)}catch(e){}
});
poll();setInterval(poll,1000);
</script>
</body></html>"""
