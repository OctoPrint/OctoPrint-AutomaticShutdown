$(function() {
    function AutomaticShutdownViewModel(parameters) {
        var self = this;

        self.printerState = parameters[0];
        self.automaticShutdown = ko.observable(false);

        self.automaticShutdown.subscribe(function(newValue){
            self.onAutomaticShutdown(newValue);
        }, self); 

        self.onAutomaticShutdown = function(value) {
            $.ajax({
                url: "api/plugin/automaticshutdown",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "automatic_shutdown",
                    value: self.automaticShutdown()
                }),
                contentType: "application/json; charset=UTF-8"
            })
        }
    }

    OCTOPRINT_VIEWMODELS.push([
        AutomaticShutdownViewModel,
        ["printerStateViewModel"],
        document.getElementById("sidebar_plugin_automaticshutdown")
    ]);
});
