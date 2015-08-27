$(function() {
    function AutomaticShutdownViewModel(parameters) {
        var self = this;

        self.automaticShutdownEnabled = ko.observable(false);
        // Hack to remove automatically added Cancel button
        // See https://github.com/sciactive/pnotify/issues/141
        PNotify.prototype.options.confirm.buttons = [];
        self.timeoutPopupText = gettext('Shutting down in ');
        self.timeoutPopupOptions = {
            title: gettext('System Shutdown'),
            icon: 'glyphicon glyphicon-question-sign',
            hide: false,
            confirm: {
                confirm: true,
                buttons: [{
                    text: 'Abort Shutdown',
                    addClass: 'btn-block btn-danger',
                    promptTrigger: true,
                    click: function(notice, value){
                        notice.remove();
                        notice.get().trigger("pnotify.cancel", [notice, value]);
                    }
                }]
            },
            buttons: {
                closer: false,
                sticker: false,
            },
            history: {
                history: false
            }
        };

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
                self.timeoutPopupOptions.text = self.timeoutPopupText + data.timeout;
                self.timeoutPopup = new PNotify(self.timeoutPopupOptions);
                self.timeoutPopup.get().on('pnotify.cancel', function() {self.abortShutdown(true);});
                self.timerInterval = window.setInterval(self.shutdownTimer, 1000);
            }
        }

        self.shutdownTimer = function() {
            self.shutdownTimeout -= 1;
            if (self.shutdownTimeout > 0) {
                self.timeoutPopupOptions.text = self.timeoutPopupText + self.shutdownTimeout;
                self.timeoutPopup.update(self.timeoutPopupOptions);
            } else {
                self.abortShutdown(false);
            }
        }

        self.abortShutdown = function(abortShutdownValue) {
            window.clearInterval(self.timerInterval);
            self.timeoutPopup.remove();
            $.ajax({
                url: "api/plugin/automaticshutdown",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "abort_shutdown",
                    value: abortShutdownValue
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
