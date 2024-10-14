const no_avg = ['333mbf', '333mbo'];

function recalcAlternating() {
    var evts = document.querySelectorAll(".evt-active.siav-active");
    for (var a = 0, leng = evts.length; a < leng; a++) {
        var visi_count = 0;
        var bgColRows = evts[a].getElementsByClassName('bgColRow');
        for (var j = 0, lengt = bgColRows.length; j < lengt; j++) {
            if (bgColRows[j].style.display != 'none') {
                if (visi_count % 2 != 0) {
                    bgColRows[j].style.backgroundColor = '#f2f2f2';
                }
                else {
                    bgColRows[j].style.backgroundColor = '#ffffff';
                }
                visi_count = visi_count + 1;
            }
        }
    }
}

function recalcVisibility() {
    var toHandle = document.querySelectorAll(".single,.average");
    var toShow = document.querySelectorAll(".ov-active.siav-active");

    for (var i = 0, len = toHandle.length; i < len; i++) {
        toHandle[i].style.display = 'none';
    }
    for (var i = 0, len = toShow.length; i < len; i++) {
        toShow[i].style.display = 'block';
    }
}

function recalcVisibilityPerS(forceSin = false) {
    if (forceSin == true) {
        // manually toggle the sin-avg-switch into single mode
        toShow = document.getElementsByClassName('single');
        toHide = document.getElementsByClassName('average');
        for (var i = 0, len = toShow.length; i < len; i++) {
            toShow[i].classList.add("siav-active");
            toShow[i].classList.remove("siav-hidden");
        }
        for (var i = 0, len = toHide.length; i < len; i++) {
            toHide[i].classList.add("siav-hidden");
            toHide[i].classList.remove("siav-active");
        }
    }
    var toHandle = document.querySelectorAll(".single,.average");
    var toShow = document.querySelectorAll(".evt-active.siav-active");

    for (var i = 0, len = toHandle.length; i < len; i++) {
        toHandle[i].style.display = 'none';
    }
    for (var i = 0, len = toShow.length; i < len; i++) {
        toShow[i].style.display = 'block';
    }
}

function toggle (e) {
    var self = e.target,
        toggleClass = '.' + self.value,
        toToggle = document.querySelectorAll(toggleClass);
    for (var i = 0, len = toToggle.length; i < len; i++) {
        toToggle[i].style.display = self.checked ? 'table-row' : 'none';
    }
    recalcAlternating();
}

function toggleRepr (e) {
    if (e.target.checked) {
        // show all of them
        var toShow = document.getElementsByClassName('allRepr');
        var toHide = document.getElementsByClassName('deRepr');
    } else {
        // show only de
        var toShow = document.getElementsByClassName('deRepr');
        var toHide = document.getElementsByClassName('allRepr');
    }
    for (var i = 0, len = toShow.length; i < len; i++) {
        toShow[i].classList.add("ov-active");
        toShow[i].classList.remove("ov-hidden");
    }
    for (var i = 0, len = toHide.length; i < len; i++) {
        toHide[i].classList.add("ov-hidden");
        toHide[i].classList.remove("ov-active");
    }
    recalcVisibility();
}

function toggleSIAV (e) {
    if (e.target.checked) {
        // show average
        toShow = document.getElementsByClassName('average');
        toHide = document.getElementsByClassName('single');
    } else {
        // show single
        toShow = document.getElementsByClassName('single');
        toHide = document.getElementsByClassName('average');
    }
    for (var i = 0, len = toShow.length; i < len; i++) {
        toShow[i].classList.add("siav-active");
        toShow[i].classList.remove("siav-hidden");
    }
    for (var i = 0, len = toHide.length; i < len; i++) {
        toHide[i].classList.add("siav-hidden");
        toHide[i].classList.remove("siav-active");
    }
    recalcVisibility();
}

function toggleSIAVPerS (e) {
    if (e.target.checked) {
        // show average
        toShow = document.getElementsByClassName('average');
        toHide = document.getElementsByClassName('single');
    } else {
        // show single
        toShow = document.getElementsByClassName('single');
        toHide = document.getElementsByClassName('average');
    }
    for (var i = 0, len = toShow.length; i < len; i++) {
        toShow[i].classList.add("siav-active");
        toShow[i].classList.remove("siav-hidden");
    }
    for (var i = 0, len = toHide.length; i < len; i++) {
        toHide[i].classList.add("siav-hidden");
        toHide[i].classList.remove("siav-active");
    }
    recalcVisibilityPerS();
    recalcAlternating();
}

var isNotCountryTogglePage = ! document.getElementById('nonDEswitch');
if (isNotCountryTogglePage == false) {
    var nonDEswitch = document.getElementById('nonDEswitch');
    nonDEswitch.addEventListener('change', toggle);
}
var isNotReprTogglePage = ! document.getElementById('allReprSwitch');
if (isNotReprTogglePage == false) {
    var allReprSwitch = document.getElementById('allReprSwitch');
    allReprSwitch.addEventListener('change', toggleRepr);
}
var isNotSinAvgTogglePage = ! document.getElementById('sinAvgSwitch');
if (isNotSinAvgTogglePage == false) {
    var sinAVGswitch = document.getElementById('sinAvgSwitch');
    sinAVGswitch.addEventListener('change', toggleSIAV);
}
var isNotSinAvgPerSTogglePage = ! document.getElementById('sinAvgSwitchPerS');
if (isNotSinAvgPerSTogglePage == false) {
    var sinAVGPerSswitch = document.getElementById('sinAvgSwitchPerS');
    sinAVGPerSswitch.addEventListener('change', toggleSIAVPerS);
}

function showEvt(ev = '333') {
    // remove active, add hidden
    const wasActive = document.querySelectorAll('.evt-active');
    for (var i = 0, len = wasActive.length; i < len; i++) {
        wasActive[i].classList.remove("evt-active");
        wasActive[i].classList.add("evt-hidden");
    }
    // for the chosen evt, the other way around
    var makeActiveSin = document.getElementsByClassName('sin-'+ev);
    if (!no_avg.includes(ev)) {
        var makeActiveAvg = document.getElementsByClassName('avg-'+ev);
    }
    makeActiveSin[0].classList.remove("evt-hidden");
    makeActiveSin[0].classList.add("evt-active");
    if (!no_avg.includes(ev)) {
        makeActiveAvg[0].classList.remove("evt-hidden");
        makeActiveAvg[0].classList.add("evt-active");
    }

    const wasActiveBtn = document.querySelectorAll('.btn-active:not(.navi-btn)');
    for (var i = 0, len = wasActiveBtn.length; i < len; i++) {
        wasActiveBtn[i].classList.remove("btn-active");
    }
    const makeActiveBtn = document.getElementById('btn-'+ev);
    makeActiveBtn.classList.add("btn-active");

    recalcAlternating();
    var sinAVGPerSlabel = document.getElementById('sinAvgLabelPerS');
    if (no_avg.includes(ev)) {
        sinAVGPerSlabel.style.display = 'none';
        var sinAVGPerSswitch = document.getElementById('sinAvgSwitchPerS');
        sinAVGPerSswitch.checked = false;
        recalcVisibilityPerS(forceSin = true);
    } else {
        sinAVGPerSlabel.style.display = 'block';
        recalcVisibilityPerS();
    }
}

// Collabsible
var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function() {
    this.classList.toggle("act");
    var content = this.nextElementSibling;
    if (content.style.maxHeight){
      content.style.maxHeight = null;
    } else {
      content.style.maxHeight = content.scrollHeight + "px";
    }
  });
}
