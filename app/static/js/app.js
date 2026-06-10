const skill = document.getElementById("skillChart");
if (skill) {
  new Chart(skill, {type: "radar", data: {labels: JSON.parse(skill.dataset.labels), datasets: [{label: "Known", data: JSON.parse(skill.dataset.values), borderColor: "#35D0FF", backgroundColor: "rgba(53,208,255,.18)"}]}, options: {plugins: {legend: {labels: {color: "#e2e8f0"}}}, scales: {r: {ticks: {color: "#94a3b8"}, grid: {color: "rgba(255,255,255,.12)"}, pointLabels: {color: "#e2e8f0"}}}}});
}
const acc = document.getElementById("accuracyChart");
if (acc) {
  new Chart(acc, {type: "doughnut", data: {labels: ["Correct", "Wrong"], datasets: [{data: [Number(acc.dataset.correct), Number(acc.dataset.wrong)], backgroundColor: ["#35D0FF", "#FF5C8A"]}]}, options: {plugins: {legend: {labels: {color: "#e2e8f0"}}}}});
}
