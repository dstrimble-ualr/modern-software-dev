// One user journey, two kinds of test.
//
//   Smoke (default: 1 virtual user for 10 seconds):
//     k6 run k6/smoke.js
//
//   Load (same journey, more users, longer), set from the command line:
//     k6 run --vus 20 --duration 1m k6/smoke.js
//     k6 run --stage 30s:20 --stage 1m:20 --stage 30s:0 k6/smoke.js    # ramp up, hold, ramp down
//
//   Another server:
//     k6 run -e BASE_URL=http://localhost:8080 k6/smoke.js
//
// Command-line flags override the `options` below. The thresholds always apply:
// if any one fails, k6 exits non-zero, and CI fails the job.
import http from 'k6/http';
import { check, group, sleep } from 'k6';

const BASE_URL = (__ENV.BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

// A refused connection has no body. Checks must return false then, not throw:
// a throw ends the iteration early, skips the sleep, and k6 spins in a tight loop.
const text = (r) => r.body || '';
const json = (r) => {
  try { return r.json(); } catch (e) { return null; }
};

export const options = {
  vus: 1,
  duration: '10s',
  thresholds: {
    checks: ['rate>0.99'],              // more than 99% of checks pass
    http_req_failed: ['rate<0.01'],     // fewer than 1% of requests fail
    http_req_duration: ['p(95)<500'],   // 95% of requests finish in under 500 ms
  },
};

export default function () {
  group('anonymous', () => {
    const page = http.get(`${BASE_URL}/`);
    check(page, {
      'login page is 200': (r) => r.status === 200,
      'login page is HTML': (r) => text(r).toLowerCase().includes('<html'),
    });

    // 401 is the right answer here, so tell k6 not to count it as a failed request.
    const blocked = http.get(`${BASE_URL}/api/widgets`, {
      responseCallback: http.expectedStatuses(401),
    });
    check(blocked, { 'widgets without a cookie is 401': (r) => r.status === 401 });
  });

  group('logged in', () => {
    // Each virtual user has its own cookie jar, like a browser, so the
    // cookie from login is sent on the requests after it.
    const login = http.post(
      `${BASE_URL}/api/login`,
      JSON.stringify({ username: 'admin', password: 'password' }),
      { headers: { 'Content-Type': 'application/json' } },
    );
    check(login, {
      'login is 200': (r) => r.status === 200,
      'login sets the token cookie': (r) => r.cookies.token !== undefined,
    });

    const widgets = http.get(`${BASE_URL}/api/widgets`);
    check(widgets, {
      'widgets is 200': (r) => r.status === 200,
      'widgets returns a list': (r) => Array.isArray(json(r)) && json(r).length > 0,
    });

    http.post(`${BASE_URL}/api/logout`);
  });

  sleep(1); // think time: real users pause between pages
}
