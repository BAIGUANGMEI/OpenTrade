import { createRouter, createWebHistory } from "vue-router";

import AuditView from "../views/AuditView.vue";
import DashboardView from "../views/DashboardView.vue";
import ModelsView from "../views/ModelsView.vue";
import StrategiesView from "../views/StrategiesView.vue";

const routes = [
  { path: "/", redirect: "/dashboard" },
  { path: "/dashboard", component: DashboardView },
  { path: "/models", component: ModelsView },
  { path: "/strategies", component: StrategiesView },
  { path: "/audit", component: AuditView },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
