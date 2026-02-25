from fastapi import APIRouter, Request
from fastapi.responses import Response

router = APIRouter(tags=["tracking"])

TRACKING_SCRIPT = """(function(){
"use strict";
var d=document,l=location,n=navigator;
var sid=d.currentScript&&d.currentScript.getAttribute("data-site");
if(!sid)return;
var ep=new URL(d.currentScript.src).origin+"/api/v1/event";
function q(k){try{var s=new URLSearchParams(l.search);return s.get(k)||""}catch(e){return""}}
function send(u){
var p=l.pathname||"/";
var r=d.referrer||"";
var w=window.innerWidth||0;
var data={
s:sid,u:l.href,p:p,r:r,
sw:w,
us:q("utm_source"),um:q("utm_medium"),uc:q("utm_campaign"),ut:q("utm_term"),ux:q("utm_content")
};
if(n.sendBeacon){n.sendBeacon(ep,JSON.stringify(data))}
else{var x=new XMLHttpRequest();x.open("POST",ep,true);x.setRequestHeader("Content-Type","application/json");x.send(JSON.stringify(data))}
}
if(d.visibilityState==="prerender"){d.addEventListener("visibilitychange",function(){if(d.visibilityState!=="prerender")send()},{once:true})}
else{send()}
var pushState=history.pushState;
if(pushState){history.pushState=function(){pushState.apply(history,arguments);send()};
window.addEventListener("popstate",function(){send()})}
})();"""


@router.get("/js/p.js")
async def tracking_script(request: Request):
    return Response(
        content=TRACKING_SCRIPT,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",
            "Content-Type": "application/javascript; charset=utf-8",
        },
    )
