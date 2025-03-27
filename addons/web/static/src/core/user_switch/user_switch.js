import { Component, useRef, useState, useEffect } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { getLastConnectedUsers, setLastConnectedUsers } from "@web/core/user";
import { imageUrl } from "@web/core/utils/urls";
import { rpc } from "@web/core/network/rpc";

export class UserSwitch extends Component {
    static template = "web.login_user_switch";
    static props = {};

    setup() {
        // Get the initial list from localStorage to keep the original functionality intact.
        const users = getLastConnectedUsers();
        this.root = useRef("root");
        this.state = useState({
            users,
            displayUserChoice: users.length > 1,
        });
        this.form = document.querySelector("form.oe_login_form");
        this.form.classList.toggle("d-none", users.length > 1);
        this.form.querySelector(":placeholder-shown")?.focus();

        // Existing effect for setting focus on the user list button.
        useEffect(
            (el) => {
                el?.querySelector("button.list-group-item-action")?.focus();
            },
            () => [this.root.el]
        );

        // Schedule asynchronous update via setTimeout (this runs after setup, outside Owl effects).
        setTimeout(() => {
            rpc("/web/get_active_users", {})
            .then((activeUsers) => {
                // Replace the users list with the fetched active users.
                this.state.users = activeUsers;
                this.state.displayUserChoice = activeUsers.length > 1;
                this.form.classList.toggle("d-none", activeUsers.length > 1);
                // Optionally update localStorage if you wish:
                setLastConnectedUsers(activeUsers);
            })
            .catch((err) => console.error("Error fetching active users", err));
        }, 0);
    }

    toggleFormDisplay() {
        this.state.displayUserChoice = !this.state.displayUserChoice && this.state.users.length;
        this.form.classList.toggle("d-none", this.state.displayUserChoice);
        this.form.querySelector(":placeholder-shown")?.focus();
    }

    getAvatarUrl({ partnerId, partnerWriteDate: unique }) {
        return imageUrl("res.partner", partnerId, "avatar_128", { unique });
    }

    remove(deletedUser) {
        this.state.users = this.state.users.filter((user) => user !== deletedUser);
        setLastConnectedUsers(this.state.users);
        if (!this.state.users.length) {
            this.fillForm();
        }
    }

    fillForm(login = "") {
        this.form.querySelector("input#login").value = login;
        this.form.querySelector("input#password").value = "";
        this.toggleFormDisplay();
    }
}

registry.category("public_components").add("web.user_switch", UserSwitch);
