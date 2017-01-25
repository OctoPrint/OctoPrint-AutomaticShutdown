$(function() {
    function AutomaticShutdownViewModel(parameters) {
        var self = this;

        self.automaticShutdownEnabled = ko.observable();

        // Hack to remove automatically added Cancel button
        // See https://github.com/sciactive/pnotify/issues/141
        PNotify.prototype.options.confirm.buttons = [];
        self.timeoutPopupText = gettext('Shutting down in ');
        self.timeoutPopupOptions = {
            title: gettext('System Shutdown'),
            type: 'notice',
            icon: true,
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
            if (self.automaticShutdownEnabled()) {
                $.ajax({
                    url: API_BASEURL + "plugin/automaticshutdown",
                    type: "POST",
                    dataType: "json",
                    data: JSON.stringify({
                        command: "enable"
                    }),
                    contentType: "application/json; charset=UTF-8"
                })
            } else {
                $.ajax({
                    url: API_BASEURL + "plugin/automaticshutdown",
                    type: "POST",
                    dataType: "json",
                    data: JSON.stringify({
                        command: "disable"
                    }),
                    contentType: "application/json; charset=UTF-8"
                })
            }
        }

        self.automaticShutdownEnabled.subscribe(self.onAutomaticShutdownEvent, self);

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "automaticshutdown") {
                return;
            }
            if (data.type == "timeout") {
                if (data.timeout_value > 0) {
                    self.timeoutPopupOptions.text = self.timeoutPopupText + data.timeout_value;
                    if (self.timeoutPopup !== undefined) {
                        self.timeoutPopup.update(self.timeoutPopupOptions);
                    } else {
                        self.timeoutPopup = new PNotify(self.timeoutPopupOptions);
                        self.timeoutPopup.get().on('pnotify.cancel', function() {self.abortShutdown(true);});
                    }
                } else {
                    self.timeoutPopup.remove();
                    self.timeoutPopup = undefined;
                }
            }
            self.automaticShutdownEnabled(data.automaticShutdownEnabled);
        }

        self.abortShutdown = function(abortShutdownValue) {
            self.timeoutPopup.remove();
            self.timeoutPopup = undefined;
            $.ajax({
                url: API_BASEURL + "plugin/automaticshutdown",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "abort"
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
