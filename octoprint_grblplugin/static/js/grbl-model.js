/**
 * Created by njones on 2/5/15.
 */

function GrblPluginViewModel(loginStateViewModel) {
    var self = this;

    self.loginState = loginStateViewModel;

    self.workPosition = ko.observable(undefined);
    self.machinePosition = ko.observable(undefined);

    self.trimFloats = ko.observable(undefined);
    self.floatPrecision = ko.observable(undefined);


    self.fromFeedbackCommandData = function(data) {
        if (data.name.slice(0,1)=="M")
            self.machinePosition(data.output);
        else if (data.name.slice(0,1) == "W")
            self.workPosition(data.output);
    };
}

ADDITIONAL_VIEWMODELS.push([GrblPluginViewModel, ["loginStateViewModel"], document.getElementById("sidebar_plugin_grblplugin")]);
