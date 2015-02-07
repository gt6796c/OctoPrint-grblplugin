/**
 * Created by njones on 2/5/15.
 */

function CncPositionViewModel(loginStateViewModel) {
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

//ADDITIONAL_VIEWMODELS.push([CncPositionViewModel, ["loginStateViewModel"], document.getElementById("settings_plugin_cncplugin")]);
ADDITIONAL_VIEWMODELS.push([CncPositionViewModel, ["loginStateViewModel"], document.getElementById("sidebar_plugin_cncplugin")]);
