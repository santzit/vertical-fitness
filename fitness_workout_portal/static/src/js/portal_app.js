/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { WorkoutPortalStore } from "./portal_store";

export class WorkoutDashboard extends Component {
    setup() {
        this.store = useState(WorkoutPortalStore);
        onMounted(async () => {
            await this.store.fetchDashboard();
        });
    }

    get dashboard() {
        return this.store.state.dashboard;
    }

    get loading() {
        return this.store.state.loading;
    }

    get error() {
        return this.store.state.error;
    }
}

WorkoutDashboard.template = "fitness_workout_portal.WorkoutDashboard";

export class WorkoutRoutinesList extends Component {
    setup() {
        this.store = useState(WorkoutPortalStore);
        onMounted(async () => {
            await this.store.fetchRoutines();
        });
    }

    get routines() {
        return this.store.state.routines;
    }

    get loading() {
        return this.store.state.loading;
    }
}

WorkoutRoutinesList.template = "fitness_workout_portal.WorkoutRoutinesList";

export class WorkoutRoutineDetail extends Component {
    setup() {
        this.store = useState(WorkoutPortalStore);
        const routineId = this.props.routineId;
        onMounted(async () => {
            if (routineId) {
                await this.store.fetchRoutineDetail(routineId);
            }
        });
    }

    get routine() {
        return this.store.state.currentRoutine;
    }

    get loading() {
        return this.store.state.loading;
    }
}

WorkoutRoutineDetail.template = "fitness_workout_portal.WorkoutRoutineDetail";

export class WorkoutExerciseDetail extends Component {
    setup() {
        this.store = useState(WorkoutPortalStore);
        const exerciseId = this.props.exerciseId;
        onMounted(async () => {
            if (exerciseId) {
                await this.store.fetchExerciseDetail(exerciseId);
            }
        });
    }

    get exercise() {
        return this.store.state.currentExercise;
    }

    get loading() {
        return this.store.state.loading;
    }
}

WorkoutExerciseDetail.template = "fitness_workout_portal.WorkoutExerciseDetail";

// Register components for use in templates
registry.category("public_components").add(
    "fitness_workout_portal.WorkoutDashboard",
    WorkoutDashboard
);
registry.category("public_components").add(
    "fitness_workout_portal.WorkoutRoutinesList",
    WorkoutRoutinesList
);
registry.category("public_components").add(
    "fitness_workout_portal.WorkoutRoutineDetail",
    WorkoutRoutineDetail
);
registry.category("public_components").add(
    "fitness_workout_portal.WorkoutExerciseDetail",
    WorkoutExerciseDetail
);
