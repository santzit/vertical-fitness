/** @odoo-module **/

export const WorkoutPortalStore = {
  state: {
    dashboard: null,
    routines: [],
    currentRoutine: null,
    currentExercise: null,
    loading: false,
    error: null,
  },

  async fetchDashboard() {
    this.state.loading = true;
    this.state.error = null;
    try {
      const response = await fetch("/my/workouts/api/dashboard");
      if (!response.ok) throw new Error("Failed to load dashboard");
      this.state.dashboard = await response.json();
    } catch (e) {
      this.state.error = e.message;
    } finally {
      this.state.loading = false;
    }
  },

  async fetchRoutines(limit = 50, offset = 0) {
    this.state.loading = true;
    this.state.error = null;
    try {
      const response = await fetch(
        `/my/workouts/api/routines?limit=${limit}&offset=${offset}`,
      );
      if (!response.ok) throw new Error("Failed to load routines");
      const data = await response.json();
      this.state.routines = data.results || [];
    } catch (e) {
      this.state.error = e.message;
    } finally {
      this.state.loading = false;
    }
  },

  async fetchRoutineDetail(routineId) {
    this.state.loading = true;
    this.state.error = null;
    try {
      const response = await fetch(`/my/workouts/api/routines/${routineId}`);
      if (!response.ok) throw new Error("Failed to load routine");
      this.state.currentRoutine = await response.json();
    } catch (e) {
      this.state.error = e.message;
    } finally {
      this.state.loading = false;
    }
  },

  async fetchExerciseDetail(exerciseId) {
    this.state.loading = true;
    this.state.error = null;
    try {
      const response = await fetch(`/my/workouts/api/exercises/${exerciseId}`);
      if (!response.ok) throw new Error("Failed to load exercise");
      this.state.currentExercise = await response.json();
    } catch (e) {
      this.state.error = e.message;
    } finally {
      this.state.loading = false;
    }
  },
};
