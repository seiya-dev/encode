# Do LoadPluginList
function LoadPluginList(string txtlist){
    fileList = RT_ReadTxtFromFile(txtlist)
    fileListLen = RT_TxtQueryLines(fileList)
    for(i = 0, fileListLen - 1){
        filePath = RT_TxtGetLine(fileList, i)
        if(filePath != "" && LeftStr(filePath, 1) != "#" && Exist(filePath)){
            fileType = RT_GetFileExtension(filePath)
            fileType == ".avs"  ? Import(filePath)     : NOP
            fileType == ".avsi" ? Import(filePath)     : NOP
            fileType == ".dll"  ? LoadPlugin(filePath) : NOP
        }
    }
    return last
}

# Do LoadPlugins
LoadPlugin("./av-plugins/RT_Stats_x64.dll")
LoadPluginList("./av-loader.txt")
