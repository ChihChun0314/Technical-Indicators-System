$(document).ready((function () {

    //Kendo Window
    var createBookWindow = $("#window");
    createBookWindow.kendoWindow({
        width: "650px",
        visible: false,
        actions: [
            "Refresh",
            "Minimize",
            "Maximize",
            "Close"
        ],
    });

    $('#create_HQMBuyStockBox').on("click", function (e) {
        createBookWindow.data("kendoWindow").center().open();
    });

}));