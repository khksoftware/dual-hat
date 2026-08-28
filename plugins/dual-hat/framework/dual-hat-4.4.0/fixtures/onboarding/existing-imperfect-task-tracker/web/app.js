// SPDX-License-Identifier: Apache-2.0
// Deliberate fixture defect: presentation and persistence assumptions are not separated.
document.querySelector("#tasks").innerHTML = localStorage.getItem("tasks") || "No tasks";
