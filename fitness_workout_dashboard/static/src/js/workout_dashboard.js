/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class WorkoutDashboard extends Component {
  static template = "fitness_workout_dashboard.WorkoutDashboard";
  static components = { Layout };
  static props = ["*"];

  setup() {
    this.orm = useService("orm");
    this.state = useState({
      loading: true,
      error: null,
      data: {
        kpis: {
          active_members: 0,
          overdue_members: 0,
          pending_memberships: 0,
          due_today_cards: 0,
          overdue_cards: 0,
        },
        trend: [],
        next_expiring_members: [],
        recent_membership_invoices: [],
        trainer_ranking: [],
      },
    });

    onWillStart(async () => {
      await this.loadData();
    });
  }

  get display() {
    return { controlPanel: {} };
  }

  async loadData() {
    try {
      this.state.loading = true;
      this.state.error = null;
      this.state.data = await this.orm.call(
        "fitness.workout.dashboard",
        "get_dashboard_data",
        [],
      );
    } catch (error) {
      this.state.error = error.message || "Could not load dashboard data.";
    } finally {
      this.state.loading = false;
    }
  }
}

registry
  .category("actions")
  .add("fitness_workout_dashboard.action", WorkoutDashboard);
