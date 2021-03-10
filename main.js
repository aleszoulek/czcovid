var ctx = document.getElementById('myChart');
var myChart = new Chart(ctx, {
    type: 'line',
    data: data,
    options: {
        title:{
            display: true,
            text: 'Covid 19 v ČR: Počet umrtí denně vs procento lidí s alespoň první dávkou vakcíny.',
        },
        scales: {
            xAxes: [{
                type: 'time',
                time: {
                    unit: 'day'
                }
            }],
            yAxes: [{
                type: 'linear', // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                display: true,
                position: 'left',
                id: 'y-axis-deaths',
            }, {
                type: 'linear', // only linear but allow scale type registration. This allows extensions to exist solely for log scale for instance
                display: true,
                position: 'right',
                id: 'y-axis-jabs',

                // grid line settings
                gridLines: {
                  drawOnChartArea: true, // only want the grid lines for one axis to show up
                },
            }],
        }
    }
});
