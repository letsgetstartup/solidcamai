import Head from 'next/head';
import { useTranslation } from '../context/TranslationContext';
import { useEffect, useState } from 'react';

export default function Home() {
  const { t, setLocale, locale } = useTranslation();
  const [machines, setMachines] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Mock fetching from v1 API
  useEffect(() => {
    const fetchMachines = async () => {
      // In real scenario, this would be: fetch("/v1/tenants/tenant_demo/sites/site_01/machines")
      // For demo, we simulate the API response
      setTimeout(() => {
        setMachines([
          { id: "fanuc_01", name: "Fanuc Robodrill v1", status: "online", load: 45, feed: 1200 },
          { id: "haas_02", name: "Haas VF-2SS", status: "idle", load: 0, feed: 0 },
          { id: "mazak_03", name: "Mazak Integrex", status: "offline", load: 0, feed: 0 }
        ]);
        setLoading(false);
      }, 800);
    };
    fetchMachines();
  }, []);

  return (
    <div className="container">
      <Head>
        <title>{t('app_name')}</title>
      </Head>

      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px', paddingTop: '20px' }}>
        <h1 className="title-gradient">{t('app_name')}</h1>
        <div className="glass" style={{ padding: '5px 10px' }}>
          <button onClick={() => setLocale('en')} style={{ background: 'none', border: 'none', color: locale === 'en' ? '#00d4ff' : '#fff', cursor: 'pointer', fontWeight: 'bold' }}>EN</button>
          <span style={{ margin: '0 5px' }}>|</span>
          <button onClick={() => setLocale('he')} style={{ background: 'none', border: 'none', color: locale === 'he' ? '#00d4ff' : '#fff', cursor: 'pointer', fontWeight: 'bold' }}>עב</button>
        </div>
      </header>

      <main>
        <section style={{ marginBottom: '40px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
            <h2 className="title-gradient">{t('nav_machines')}</h2>
            <div className="glass" style={{ padding: '5px 15px', color: '#00d4ff' }}>{machines.length} Total</div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            {machines.map((m: any) => (
              <div key={m.id} className="machine-card glass">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '15px' }}>
                  <div>
                    <h3 style={{ fontSize: '1.2rem' }}>{m.name}</h3>
                    <code style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{m.id}</code>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center' }}>
                    <span className={`status-indicator status-${m.status}`}></span>
                    <span style={{ fontSize: '0.9rem', textTransform: 'uppercase' }}>{t(`status_${m.status}`)}</span>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                  <div style={{ padding: '10px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Spindle Load</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: m.load > 80 ? 'var(--error-color)' : 'var(--success-color)' }}>{m.load}%</div>
                  </div>
                  <div style={{ padding: '10px', background: 'rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Feed Rate</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'var(--accent-color)' }}>{m.feed}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="glass" style={{ padding: '20px' }}>
          <h2 className="title-gradient" style={{ marginBottom: '20px' }}>{t('event_timeline')}</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {[1, 2, 3].map(i => (
              <div key={i} style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
                  <span style={{ fontWeight: 'bold' }}>{i === 1 ? 'ANOMALY_DETECTED' : 'STATE_CHANGED'}</span>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>2 mins ago</span>
                </div>
                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                  {i === 1 ? 'Spindle vibration exceeds threshold (8.2g)' : 'Machine haas_02 entered IDLE mode'}
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
