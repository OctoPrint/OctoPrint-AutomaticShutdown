$(function() {
    function AutomaticShutdownViewModel(parameters) {
        var self = this;

        self.automaticShutdownEnabled = ko.observable(false);

        self.onAutomaticShutdownEvent = function() {
            $.ajax({
                url: "api/plugin/automaticshutdown",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "automatic_shutdown",
                    value: self.automaticShutdownEnabled()
                }),
                contentType: "application/json; charset=UTF-8"
            })
        }

        self.automaticShutdownEnabled.subscribe(self.onAutomaticShutdownEvent, self);

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "automaticshutdown") {
                return;
            }
            if (data.type == "timeout") {
                self.shutdownTimeout = data.timeout;
                self.timeoutPopup = new PNotify({
                    title: 'System Shutdown',
                    text: 'Shutting down in ' + self.shutdownTimeout + '...',
                    icon: 'glyphicon glyphicon-question-sign',
                    hide: false,
                    confirm: {
                        confirm: true
                    },
                    buttons: {
                        closer: false,
                        sticker: false
                    },
                    history: {
                        history: false
                    }
                })
                self.timeoutPopup.get().on('pnotify.confirm', function() {self.confirmShutdown(true);});
                self.timeoutPopup.get().on('pnotify.cancel', function() {self.confirmShutdown(false);});
                self.timerInterval = window.setInterval(self.shutdownTimer, 1000);
            }
        }

        self.shutdownTimer = function() {
            self.shutdownTimeout -= 1;
            if (self.shutdownTimeout > 0) {
                self.timeoutPopup.update({
                    title: 'System Shutdown',
                    text: 'Shutting down in ' + self.shutdownTimeout + '...',
                    icon: 'glyphicon glyphicon-question-sign',
                    hide: false,
                    confirm: {
                        confirm: true
                    },
                    buttons: {
                        closer: false,
                        sticker: false
                    },
                    history: {
                        history: false
                    }
                });
            } else {
                self.confirmShutdown(true);
            }
        }

        self.confirmShutdown = function(confirmShutdownValue) {
            window.clearInterval(self.timerInterval);
            self.timeoutPopup.remove();
            $.ajax({
                url: "api/plugin/automaticshutdown",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "confirm_shutdown",
                    value: confirmShutdownValue
                }),
                contentType: "application/json; charset=UTF-8"
            })
        }
    }

    OCTOPRINT_VIEWMODELS.push([
        AutomaticShutdownViewModel,
        [],
        document.getElementById("sidebar_plugin_automaticshutdown")
    ]);
});
