let stockChart = null;

// Safe DOM-get helper
const $ = (id) => document.getElementById(id);

// Scroll helpers for page-control
function initPageControl() {
  const home = $('home');
  const pred = $('prediction');
  $('btn-home').addEventListener('click', () => home.scrollIntoView({ behavior: 'smooth' }));
  $('btn-pred').addEventListener('click', () => pred.scrollIntoView({ behavior: 'smooth' }));
}

// Fetch and update UI
async function fetchData() {
  
  try {
    
    const res = await fetch("http://127.0.0.1:8000/latest");
    
    if (!res.ok) throw new Error("Network response not ok");
    
    const data = await res.json();
    console.log('API:', data);

    // Stats
    $('total-buys').textContent = data.total_buys ?? '—';
    $('correct-buys').textContent = data.correct_buys ?? '—';
    $('win-percent').textContent = (data.win_percent ?? '—') + '%';

    // Recommendation card
    $('next-date').textContent = `Next Market Open: ${data.next_date ?? '--'}`;
    if (data.buy_signal) {
      $('recommendation-card').classList.add('buy-day');
      $('recommendation-card').classList.remove('neutral-day');
      $('recommendation-text').textContent = "Tomorrow is a BUY day ↑";
      //$('probability').textContent = `Prob: ${(Math.round((data.prediction_probability ?? data.pred_prob ?? 0) * 10000) / 100)}%`;
    } else {
      $('recommendation-card').classList.add('neutral-day');
      $('recommendation-card').classList.remove('buy-day');
      $('recommendation-text').textContent = "Tomorrow is NOT a buy day";
      //$('probability').textContent = `Prob: ${(Math.round((data.prediction_probability ?? data.pred_prob ?? 0) * 10000) / 100)}%`;
    }

    // Last updated
    $('last-updated').textContent = new Date().toLocaleString();

    // Chart update (smaller chart in prediction panel)
    const labels = data.last_month_dates ?? [];
    const values = data.last_month_close ?? [];

    const ctx = document.getElementById('stockChart').getContext('2d');

    // create or update chart
    if (stockChart) {
      stockChart.data.labels = labels;
      stockChart.data.datasets[0].data = values;
      stockChart.update();
    } else {
      stockChart = new Chart(ctx, {
        type: 'line',
        data: {
          labels: labels,
          datasets: [{
            label: 'Close Price',
            data: values,
            borderColor: '#1fc27a',
            backgroundColor: 'rgba(31,194,122,0.08)',
            pointBackgroundColor: '#fff',
            pointBorderColor: '#1fc27a',
            tension: 0.28,
            fill: true,
            pointRadius: 3,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              mode: 'index',
              intersect: false,
              callbacks: {
                label: function(context) {
                  return `Close: $${context.parsed.y.toFixed(2)}`;
                }
              }
            }
          },
          scales: {
            x: { display: true, title: { display: false }, grid: { display: false } },
            y: { display: true, title: { display: false }, ticks: { callback: v => `$${v}` } }
          }
        }
      });
    }

  } catch (err) {
    console.error("fetchData error:", err);
  }
}

// Initialize when DOM ready
window.addEventListener('DOMContentLoaded', () => {
  initPageControl();
  fetchData();                 // initial
  setInterval(fetchData, 10000); // for testing: every 10s
});