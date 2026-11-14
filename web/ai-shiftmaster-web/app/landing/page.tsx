'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import {
  AlertOutlined,
  ArrowRightOutlined,
  BarChartOutlined,
  BellOutlined,
  CalendarOutlined,
  ApartmentOutlined,
  CheckCircleFilled,
  ClockCircleOutlined,
  CloudSyncOutlined,
  GithubOutlined,
  HeartOutlined,
  LockOutlined,
  MobileOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
  ThunderboltOutlined,
  UserAddOutlined,
} from '@ant-design/icons';
import './landing.css';

/* ------------------------------------------------------------------ */
/* Small helpers                                                       */
/* ------------------------------------------------------------------ */

/** Adds `is-visible` to children with `.reveal` when they scroll into view. */
function useReveal() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    const items = root.querySelectorAll<HTMLElement>('.reveal');
    if (!('IntersectionObserver' in window)) {
      items.forEach((el) => el.classList.add('is-visible'));
      return;
    }
    const observer = new IntersectionObserver(
      (entries) =>
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        }),
      { threshold: 0.15 }
    );
    items.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);
  return ref;
}

/** Counts up to `to` once visible. */
function CountUp({ to, decimals = 0, suffix = '' }: { to: number; decimals?: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [value, setValue] = useState(0);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let frame = 0;
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return;
      observer.disconnect();
      if (reduce) {
        setValue(to);
        return;
      }
      const start = performance.now();
      const tick = (now: number) => {
        const t = Math.min((now - start) / 1400, 1);
        setValue(to * (1 - Math.pow(1 - t, 3)));
        if (t < 1) frame = requestAnimationFrame(tick);
      };
      frame = requestAnimationFrame(tick);
    });
    observer.observe(el);
    return () => {
      observer.disconnect();
      cancelAnimationFrame(frame);
    };
  }, [to]);
  return <span ref={ref}>{value.toFixed(decimals)}{suffix}</span>;
}

/* ------------------------------------------------------------------ */
/* Content                                                             */
/* ------------------------------------------------------------------ */

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const PEOPLE = ['Hannah S.', 'Omar H.', 'Grace K.', 'Leo M.', 'Ines C.'];
// m = morning, d = day, e = evening, n = night, '' = day off
const PLAN = [
  ['m', 'm', 'm', '', 'm', 'd', ''],
  ['e', 'e', '', 'e', 'e', '', 'e'],
  ['d', 'd', 'd', 'd', '', '', 'd'],
  ['', 'n', 'n', 'n', 'n', '', ''],
  ['m', '', 'd', 'm', 'm', 'm', ''],
];
const SHIFT_NAME: Record<string, string> = { m: 'Morning', d: 'Day', e: 'Evening', n: 'Night' };

const FEATURES = [
  { icon: <RobotOutlined />, title: 'AI schedule optimization', text: 'Fill every slot with the best-fitting people, scored on preferences and workload balance.' },
  { icon: <SafetyCertificateOutlined />, title: 'Labor rules built in', text: 'Weekly hour caps, minimum rest and consecutive-day limits are enforced, not suggested.' },
  { icon: <HeartOutlined />, title: 'Preferences that count', text: 'Preferred shifts and weekly days off are part of the objective from the start.' },
  { icon: <AlertOutlined />, title: 'Conflict detection', text: 'Overlaps, overtime and understaffed slots are flagged before you publish.' },
  { icon: <BarChartOutlined />, title: 'Live workforce analytics', text: 'Coverage, planned hours and shift mix for any week or month, exportable to Excel.' },
  { icon: <BellOutlined />, title: 'Notifications built in', text: 'In-app notifications for managers, push notifications and background sync on the mobile app.' },
];

const STEPS = [
  { n: '01', title: 'Create your workspace', text: 'Sign up with your company name. You become the administrator and add your team and departments.' },
  { n: '02', title: 'Set rules & generate', text: 'Choose shift types, staffing ranges and labor limits. The optimizer builds the schedule and explains its trade-offs.' },
  { n: '03', title: 'Review & publish', text: 'Check warnings, export or save. Employees see their shifts and set preferences in the mobile app.' },
];

const STACK = ['FastAPI', 'PostgreSQL', 'SQLAlchemy', 'Next.js 16', 'React 19', 'TypeScript', 'Ant Design', 'Flutter', 'Playwright', 'Docker'];

export default function LandingPage() {
  const pageRef = useReveal();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <div className="lp" ref={pageRef}>
      {/* ------------------------------------------------ Navigation */}
      <header className={`lp-nav ${scrolled ? 'is-scrolled' : ''}`}>
        <div className="lp-container lp-nav-inner">
          <Link href="/landing" className="lp-brand">
            <span className="lp-brand-mark"><CalendarOutlined /></span>
            ShiftMaster AI
          </Link>
          <nav className="lp-links">
            <a href="#features">Features</a>
            <a href="#how">How it works</a>
            <a href="#mobile">Mobile</a>
            <a href="#workspaces">Workspaces</a>
          </nav>
          <div className="lp-nav-cta">
            <Link href="/login" className="lp-btn lp-btn-ghost">Sign in</Link>
            <Link href="/register" className="lp-btn lp-btn-primary">Get started</Link>
          </div>
        </div>
      </header>

      {/* ------------------------------------------------ Hero */}
      <section className="lp-hero">
        <div className="lp-blob lp-blob-a" />
        <div className="lp-blob lp-blob-b" />
        <div className="lp-grid-bg" />

        <div className="lp-container lp-hero-inner">
          <div className="lp-hero-copy">
            <span className="lp-pill lp-fade" style={{ animationDelay: '0ms' }}>
              <ThunderboltOutlined /> Constraint-aware scheduling engine
            </span>
            <h1 className="lp-fade" style={{ animationDelay: '80ms' }}>
              Shift plans that <span className="lp-gradient-text">respect people</span> and the rules.
            </h1>
            <p className="lp-lead lp-fade" style={{ animationDelay: '160ms' }}>
              ShiftMaster AI turns availability, preferences and labor limits into a ready-to-publish schedule in
              seconds — with a web dashboard for managers and a mobile app for every employee.
            </p>
            <div className="lp-hero-cta lp-fade" style={{ animationDelay: '240ms' }}>
              <Link href="/register" className="lp-btn lp-btn-primary lp-btn-lg">
                Start planning <ArrowRightOutlined />
              </Link>
              <Link href="/login" className="lp-btn lp-btn-light lp-btn-lg">Open the demo</Link>
            </div>
            <ul className="lp-checks lp-fade" style={{ animationDelay: '320ms' }}>
              <li><CheckCircleFilled /> Rest periods enforced</li>
              <li><CheckCircleFilled /> Preferences built in</li>
              <li><CheckCircleFilled /> Private company workspace</li>
            </ul>
          </div>

          {/* Animated product preview */}
          <div className="lp-hero-visual lp-fade" style={{ animationDelay: '200ms' }}>
            <div className="lp-window">
              <div className="lp-window-bar">
                <span /><span /><span />
                <em>Week 47 · Engineering</em>
              </div>
              <div className="lp-schedule">
                <div className="lp-schedule-head" />
                {DAYS.map((d) => <div key={d} className="lp-schedule-head">{d}</div>)}
                {PEOPLE.map((person, row) => (
                  <React.Fragment key={person}>
                    <div className="lp-schedule-name">{person}</div>
                    {PLAN[row].map((cell, col) => (
                      <div key={col} className="lp-schedule-cell">
                        {cell && (
                          <span
                            className={`lp-chip lp-chip-${cell}`}
                            style={{ animationDelay: `${600 + (col * PEOPLE.length + row) * 70}ms` }}
                          >
                            {SHIFT_NAME[cell]}
                          </span>
                        )}
                      </div>
                    ))}
                  </React.Fragment>
                ))}
              </div>
              <div className="lp-scanline" />
            </div>

            <div className="lp-float lp-float-a">
              <div className="lp-float-icon lp-green"><CheckCircleFilled /></div>
              <div>
                <strong>100% coverage</strong>
                <span>All slots filled</span>
              </div>
            </div>
            <div className="lp-float lp-float-b">
              <div className="lp-float-icon lp-pink"><HeartOutlined /></div>
              <div>
                <strong>99% preference match</strong>
                <span>Preferred shifts honoured</span>
              </div>
            </div>
            <div className="lp-float lp-float-c">
              <div className="lp-float-icon lp-blue"><ClockCircleOutlined /></div>
              <div>
                <strong>11 h minimum rest</strong>
                <span>Never violated</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------ Numbers */}
      <section className="lp-numbers">
        <div className="lp-container lp-numbers-grid">
          {[
            { value: <CountUp to={200} suffix="+" />, label: 'employees scheduled in one run' },
            { value: <CountUp to={2} suffix=" s" />, label: 'to plan a full week' },
            { value: <CountUp to={99.4} decimals={1} suffix="%" />, label: 'preference match on the demo data' },
            { value: <CountUp to={11} suffix=" h" />, label: 'minimum rest between shifts, always enforced' },
          ].map((item, i) => (
            <div className="lp-number reveal" style={{ transitionDelay: `${i * 90}ms` }} key={i}>
              <div className="lp-number-value">{item.value}</div>
              <div className="lp-number-label">{item.label}</div>
            </div>
          ))}
        </div>
        <p className="lp-footnote lp-container">Measured on the synthetic 200-person demo workforce included in the repository.</p>
      </section>

      {/* ------------------------------------------------ Features */}
      <section className="lp-section" id="features">
        <div className="lp-container">
          <div className="lp-section-head reveal">
            <span className="lp-eyebrow">Features</span>
            <h2>Everything a shift manager needs, nothing they have to babysit.</h2>
          </div>
          <div className="lp-features">
            {FEATURES.map((f, i) => (
              <div className="lp-feature reveal" key={f.title} style={{ transitionDelay: `${(i % 3) * 90}ms` }}>
                <div className="lp-feature-icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------ How it works */}
      <section className="lp-section lp-section-tint" id="how">
        <div className="lp-container">
          <div className="lp-section-head reveal">
            <span className="lp-eyebrow">How it works</span>
            <h2>From rules to a published schedule in three steps.</h2>
          </div>
          <div className="lp-steps">
            {STEPS.map((s, i) => (
              <div className="lp-step reveal" key={s.n} style={{ transitionDelay: `${i * 120}ms` }}>
                <span className="lp-step-n">{s.n}</span>
                <h3>{s.title}</h3>
                <p>{s.text}</p>
              </div>
            ))}
          </div>

          <div className="lp-score reveal">
            <div className="lp-score-copy">
              <h3>Every schedule comes with a score you can explain.</h3>
              <p>
                The optimizer reports how many required slots were filled, how often people got the shift they
                asked for, and how evenly hours are spread — so trade-offs are visible, not hidden.
              </p>
            </div>
            <div className="lp-score-bars">
              {[
                { label: 'Coverage', value: 100 },
                { label: 'Preference match', value: 99.4 },
                { label: 'Fairness', value: 84.1 },
              ].map((b) => (
                <div className="lp-bar" key={b.label}>
                  <div className="lp-bar-top"><span>{b.label}</span><strong>{b.value}%</strong></div>
                  <div className="lp-bar-track"><div className="lp-bar-fill" style={{ ['--w' as string]: `${b.value}%` }} /></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------ Mobile */}
      <section className="lp-section" id="mobile">
        <div className="lp-container lp-split">
          <div className="lp-split-copy reveal">
            <span className="lp-eyebrow">For employees</span>
            <h2>The schedule in every pocket — even offline.</h2>
            <p>
              The Flutter app shows each employee their week, lets them request leave and set shift preferences,
              and keeps working without a connection. Changes sync automatically when the device is back online.
            </p>
            <ul className="lp-list">
              <li><MobileOutlined /> Weekly shift view and notifications</li>
              <li><CalendarOutlined /> Leave requests with live status</li>
              <li><HeartOutlined /> Preferred shifts and days off</li>
              <li><CloudSyncOutlined /> Offline-first sync with retry</li>
            </ul>
          </div>
          <div className="lp-phone-wrap reveal">
            <div className="lp-phone">
              <div className="lp-phone-notch" />
              <div className="lp-phone-screen">
                <div className="lp-phone-greet">Good morning, Hannah</div>
                <div className="lp-phone-next">
                  <span>Next shift</span>
                  <strong>Tomorrow · 06:00 – 14:00</strong>
                  <em>Morning · Engineering</em>
                </div>
                {['Mon', 'Tue', 'Wed', 'Thu', 'Fri'].map((d, i) => (
                  <div className="lp-phone-row" key={d} style={{ animationDelay: `${i * 140}ms` }}>
                    <b>{d}</b>
                    <span className={`lp-chip lp-chip-${['m', 'm', 'm', '', 'm'][i] || 'off'}`}>{['Morning', 'Morning', 'Morning', 'Day off', 'Morning'][i]}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------ Workspaces */}
      <section className="lp-section lp-section-dark" id="workspaces">
        <div className="lp-container lp-split">
          <div className="lp-split-copy reveal">
            <span className="lp-eyebrow lp-eyebrow-light">Built for companies</span>
            <h2>Every company gets its own private workspace.</h2>
            <p>
              Sign up with your company name and you get a workspace that only your team can see. Data isolation
              is enforced on every database query, not left to each screen, so one company can never see
              another&rsquo;s people or schedules.
            </p>
            <ul className="lp-list lp-list-light">
              <li><LockOutlined /> Isolated data for every company</li>
              <li><UserAddOutlined /> The founder is the admin and adds the team</li>
              <li><ApartmentOutlined /> Admin, manager and employee roles</li>
              <li><MobileOutlined /> Employees sign in to the mobile app with the accounts you create</li>
            </ul>
          </div>
          <div className="lp-tenants reveal" aria-hidden="true">
            {[
              { name: 'Acme Logistics', people: ['Hannah S.', 'Omar H.', 'Grace K.'], tint: 'lp-tenant-a' },
              { name: 'Northwind Retail', people: ['Leo M.', 'Ines C.', 'Yuki T.'], tint: 'lp-tenant-b' },
            ].map((t, i) => (
              <div className={`lp-tenant ${t.tint}`} key={t.name} style={{ animationDelay: `${i * -3}s` }}>
                <div className="lp-tenant-head">
                  <span className="lp-tenant-logo">{t.name[0]}</span>
                  <div>
                    <strong>{t.name}</strong>
                    <em>Private workspace</em>
                  </div>
                  <LockOutlined className="lp-tenant-lock" />
                </div>
                {t.people.map((person, j) => (
                  <div className="lp-tenant-row" key={person}>
                    <span>{person}</span>
                    <span className={`lp-chip lp-chip-${['m', 'd', 'e'][(i + j) % 3]}`}>{['Morning', 'Day', 'Evening'][(i + j) % 3]}</span>
                  </div>
                ))}
              </div>
            ))}
            <div className="lp-tenant-wall"><LockOutlined /> Isolated</div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------ Stack */}
      <section className="lp-stack">
        <div className="lp-container">
          <p className="lp-stack-title">Built with a modern, open stack</p>
          <div className="lp-marquee">
            <div className="lp-marquee-track">
              {[...STACK, ...STACK].map((s, i) => <span key={i}>{s}</span>)}
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------ CTA */}
      <section className="lp-cta">
        <div className="lp-container lp-cta-inner reveal">
          <h2>Plan next week before your coffee gets cold.</h2>
          <p>Explore the demo workspace with 200 synthetic employees, or create a private workspace for your company.</p>
          <div className="lp-hero-cta">
            <Link href="/register" className="lp-btn lp-btn-white lp-btn-lg">Create your workspace <ArrowRightOutlined /></Link>
            <Link href="/login" className="lp-btn lp-btn-outline-light lp-btn-lg"><TeamOutlined /> Open the demo</Link>
          </div>
        </div>
      </section>

      <footer className="lp-footer">
        <div className="lp-container lp-footer-inner">
          <div className="lp-brand lp-brand-small">
            <span className="lp-brand-mark"><CalendarOutlined /></span>
            ShiftMaster AI
          </div>
          <span>© {new Date().getFullYear()} ShiftMaster AI · MIT License</span>
          <a href="https://github.com/LordAurora/shift-planning-application" target="_blank" rel="noreferrer">
            <GithubOutlined /> Source code
          </a>
        </div>
      </footer>
    </div>
  );
}
