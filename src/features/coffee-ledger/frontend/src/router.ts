import { createRouter, createWebHistory } from "vue-router";
import { isAdminRoute, isAdminUnlocked, lockAdmin } from "./adminGate";
import HomeView from "./views/HomeView.vue";
import UnlockView from "./views/UnlockView.vue";
import AdminHomeView from "./views/admin/AdminHomeView.vue";
import PeopleAdminView from "./views/admin/PeopleAdminView.vue";
import OperationsView from "./views/admin/OperationsView.vue";
import SummaryView from "./views/admin/SummaryView.vue";

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: "/", component: HomeView },
    { path: "/unlock", component: UnlockView },
    { path: "/admin", component: AdminHomeView },
    { path: "/admin/people", component: PeopleAdminView },
    { path: "/admin/summary", component: SummaryView },
    { path: "/admin/operations", component: OperationsView },
  ],
});

router.beforeEach((to) => {
  if (!isAdminRoute(to.path)) {
    lockAdmin();
    return true;
  }
  if (isAdminUnlocked()) {
    return true;
  }
  return { path: "/unlock", query: { next: to.fullPath } };
});
