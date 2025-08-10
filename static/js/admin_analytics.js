/* Chart rendering for Admin Analytics */
(function () {
  try {
    var ordersCanvas = document.getElementById('ordersChart');
    var salesCanvas = document.getElementById('salesChart');
    if (!ordersCanvas || !salesCanvas) return;

    var labels = JSON.parse(ordersCanvas.getAttribute('data-labels') || '[]');
    var ordersData = JSON.parse(ordersCanvas.getAttribute('data-orders') || '[]');
    var salesData = JSON.parse(salesCanvas.getAttribute('data-sales') || '[]');

    var ctx1 = ordersCanvas.getContext('2d');
    new Chart(ctx1, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Orders',
          data: ordersData,
          backgroundColor: '#4dd0e1'
        }]
      },
      options: { scales: { y: { beginAtZero: true } } }
    });

    var ctx2 = salesCanvas.getContext('2d');
    new Chart(ctx2, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Sales (₹)',
          data: salesData,
          borderColor: '#76ff03',
          backgroundColor: 'rgba(118,255,3,0.2)'
        }]
      },
      options: { scales: { y: { beginAtZero: true } } }
    });
  } catch (err) {
    console.error('Analytics charts failed to render', err);
  }
})();

