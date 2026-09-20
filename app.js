/* =========================================================
   Smart Career Planner - small vanilla JavaScript helpers
   (no libraries needed). Every block only runs if its
   elements exist on the current page.
   ========================================================= */
document.addEventListener('DOMContentLoaded', function () {

    var $ = function (sel, root) { return (root || document).querySelector(sel); };
    var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

    /* ---------- 1. Dark / light theme toggle ---------- */
    var themeBtn = $('#themeToggle');
    if (themeBtn) {
        themeBtn.addEventListener('click', function () {
            var next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
            document.documentElement.dataset.theme = next;
            try { localStorage.setItem('theme', next); } catch (e) {}
        });
    }

    /* ---------- 2. Mobile menu ---------- */
    var navBtn = $('#navToggle'), navLinks = $('#navLinks');
    if (navBtn && navLinks) {
        navBtn.addEventListener('click', function () {
            var open = navLinks.classList.toggle('open');
            navBtn.setAttribute('aria-expanded', open);
        });
    }

    /* ---------- 3. Toast messages (auto-hide after 4.5s) ---------- */
    function closeToast(t) {
        t.classList.add('leaving');
        setTimeout(function () { t.remove(); }, 300);
    }
    $$('.toast').forEach(function (t) {
        $('.toast-x', t).addEventListener('click', function () { closeToast(t); });
        setTimeout(function () { closeToast(t); }, 4500);
    });

    /* ---------- 4. Reveal cards when they scroll into view ---------- */
    var reveals = $$('.reveal');
    if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (e) {
                if (e.isIntersecting) {
                    e.target.classList.add('in');
                    io.unobserve(e.target);
                    setTimeout(function () {            // after the reveal, give hover effects back
                        e.target.style.transitionDelay = '';
                        e.target.classList.add('settled');
                    }, 1000);
                }
            });
        }, { threshold: 0.12 });
        reveals.forEach(function (el, i) {
            el.style.transitionDelay = (i % 4) * 70 + 'ms';   // small stagger
            io.observe(el);
        });
    } else {
        reveals.forEach(function (el) { el.classList.add('in'); });
    }

    /* ---------- 5. Count-up numbers on the dashboard ---------- */
    $$('[data-count]').forEach(function (el) {
        var target = parseInt(el.dataset.count, 10) || 0;
        var suffix = el.dataset.suffix || '';
        if (target === 0) { el.textContent = '0' + suffix; return; }
        var start = null, duration = 900;
        function tick(ts) {
            if (start === null) start = ts;
            var p = Math.min((ts - start) / duration, 1);
            var eased = 1 - Math.pow(1 - p, 3);
            el.textContent = Math.round(target * eased) + suffix;
            if (p < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    });

    /* ---------- 6. Radar chart (dashboard) ---------- */
    var radar = $('#radar');
    if (radar) {
        var data = JSON.parse(radar.dataset.radar);
        var NS = 'http://www.w3.org/2000/svg';
        var cx = 260, cy = 175, R = 108, n = data.length;
        function pt(i, value) {                       // value 0..1 -> x,y
            var a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
            return [cx + Math.cos(a) * R * value, cy + Math.sin(a) * R * value];
        }
        function el(name, attrs, text) {
            var e = document.createElementNS(NS, name);
            for (var k in attrs) e.setAttribute(k, attrs[k]);
            if (text) e.textContent = text;
            return e;
        }
        // background rings (25/50/75/100 %)
        [0.25, 0.5, 0.75, 1].forEach(function (lvl) {
            var pts = data.map(function (_, i) { return pt(i, lvl).join(','); }).join(' ');
            radar.appendChild(el('polygon', { points: pts, 'class': 'grid-line' }));
        });
        [50, 100].forEach(function (v) {
            var p = pt(0, v / 100);
            radar.appendChild(el('text', { x: p[0] + 5, y: p[1] + 3, 'class': 'scale' }, v + '%'));
        });
        // axes + labels
        data.forEach(function (d, i) {
            var end = pt(i, 1), lab = pt(i, 1.2);
            radar.appendChild(el('line', { x1: cx, y1: cy, x2: end[0], y2: end[1], 'class': 'axis' }));
            var anchor = Math.abs(lab[0] - cx) < 8 ? 'middle' : (lab[0] > cx ? 'start' : 'end');
            radar.appendChild(el('text', { x: lab[0], y: lab[1] + 4, 'text-anchor': anchor }, d.label));
        });
        // the data shape (animated in)
        var g = el('g', { 'class': 'radar-in' });
        g.appendChild(el('polygon', {
            points: data.map(function (d, i) { return pt(i, Math.max(d.score, 3) / 100).join(','); }).join(' '),
            'class': 'shape'
        }));
        data.forEach(function (d, i) {
            var p = pt(i, Math.max(d.score, 3) / 100);
            var c = el('circle', { cx: p[0], cy: p[1], r: 4.5, 'class': 'pt' });
            c.appendChild(el('title', {}, d.label + ': ' + d.score + '%'));
            g.appendChild(c);
        });
        radar.appendChild(g);
    }

    /* ---------- 7. Careers page: search, filter, sort ---------- */
    var careerGrid = $('#careerGrid');
    if (careerGrid) {
        var cards = $$('.career-card', careerGrid);
        var search = $('#careerSearch'), sort = $('#careerSort'), empty = $('#careerEmpty');
        var filter = 'all';

        function applyCareers() {
            var q = search.value.trim().toLowerCase(), shown = 0;
            cards.forEach(function (c) {
                var score = parseInt(c.dataset.score, 10);
                var ok = c.dataset.name.indexOf(q) !== -1 &&
                    (filter === 'all' || (filter === 'strong' && score >= 50) || (filter === 'low' && score < 50));
                c.style.display = ok ? '' : 'none';
                if (ok) shown++;
            });
            var ordered = cards.slice().sort(function (a, b) {
                return sort.value === 'name'
                    ? a.dataset.name.localeCompare(b.dataset.name)
                    : (b.dataset.score - a.dataset.score) || a.dataset.name.localeCompare(b.dataset.name);
            });
            ordered.forEach(function (c) { careerGrid.appendChild(c); });
            empty.hidden = shown !== 0;
        }
        search.addEventListener('input', applyCareers);
        sort.addEventListener('change', applyCareers);
        $$('#careerFilters .pill-btn').forEach(function (b) {
            b.addEventListener('click', function () {
                $$('#careerFilters .pill-btn').forEach(function (x) { x.classList.remove('active'); });
                b.classList.add('active');
                filter = b.dataset.filter;
                applyCareers();
            });
        });
    }

    /* ---------- 8. Skills page: search, group select, live preview ---------- */
    var form = $('#skillsForm');
    if (form) {
        var careers = JSON.parse($('#careerData').textContent);
        var boxes = $$('input[type=checkbox]', form);
        var preview = $('#previewList'), count = $('#selCount');

        function selectedSet() {
            var s = {};
            boxes.forEach(function (b) { if (b.checked) s[b.value.toLowerCase()] = true; });
            return s;
        }
        function refresh() {
            var sel = selectedSet();
            count.textContent = Object.keys(sel).length;

            // per-group counters + button text
            $$('[data-group]').forEach(function (g) {
                var gb = $$('input[type=checkbox]', g);
                var on = gb.filter(function (b) { return b.checked; }).length;
                $('[data-group-count]', g).textContent = on + '/' + gb.length;
                $('[data-toggle-group]', g).textContent = on === gb.length ? 'Clear' : 'Select all';
            });

            // live career scores (same formula as the server: matched / required)
            var scored = careers.map(function (c) {
                var m = c.skills.filter(function (s) { return sel[s.toLowerCase()]; }).length;
                return { name: c.name, icon: c.icon, score: Math.round(m / c.skills.length * 100) };
            }).sort(function (a, b) { return b.score - a.score || a.name.localeCompare(b.name); });

            // update existing rows (keeps the width animation smooth)
            if (!preview.children.length) {
                scored.slice(0, 4).forEach(function () {
                    var row = document.createElement('div');
                    row.className = 'pv-row';
                    row.innerHTML = '<div class="pv-top"><span></span><span></span></div><div class="progress"><div></div></div>';
                    preview.appendChild(row);
                });
            }
            scored.slice(0, 4).forEach(function (c, i) {
                var row = preview.children[i], spans = row.querySelectorAll('.pv-top span');
                spans[0].textContent = c.icon + ' ' + c.name;
                spans[1].textContent = c.score + '%';
                row.querySelector('.progress > div').style.width = c.score + '%';
            });
        }

        boxes.forEach(function (b) { b.addEventListener('change', refresh); });

        $('#clearAll').addEventListener('click', function () {
            boxes.forEach(function (b) { b.checked = false; });
            refresh();
        });

        $$('[data-toggle-group]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var gb = $$('input[type=checkbox]', btn.closest('[data-group]'));
                var all = gb.every(function (b) { return b.checked; });
                gb.forEach(function (b) { b.checked = !all; });
                refresh();
            });
        });

        $('#skillSearch').addEventListener('input', function (e) {
            var q = e.target.value.trim().toLowerCase(), any = false;
            $$('.skill-option').forEach(function (o) {
                var ok = o.dataset.skill.indexOf(q) !== -1;
                o.classList.toggle('hide', !ok);
                if (ok) any = true;
            });
            $$('[data-group]').forEach(function (g) {
                g.hidden = !$$('.skill-option:not(.hide)', g).length;
            });
            $('#noSkills').hidden = any;
        });

        refresh();
    }

    /* ---------- 9. Password show/hide + strength meter ---------- */
    $$('.pw-toggle').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var input = document.getElementById(btn.dataset.target);
            var show = input.type === 'password';
            input.type = show ? 'text' : 'password';
            btn.textContent = show ? 'Hide' : 'Show';
        });
    });

    var strength = $('#strength');
    if (strength) {
        var labels = ['Use letters, numbers and symbols for a stronger password.', 'Weak', 'Okay', 'Good', 'Strong 💪'];
        document.getElementById('password').addEventListener('input', function (e) {
            var v = e.target.value, score = 0;
            if (v.length >= 6) score++;
            if (v.length >= 10) score++;
            if (/[A-Z]/.test(v) && /[a-z]/.test(v)) score++;
            if (/\d/.test(v) && /[^A-Za-z0-9]/.test(v)) score++;
            if (!v) score = 0;
            strength.dataset.level = score;
            $('#strengthLabel').textContent = labels[score];
        });
    }
});
