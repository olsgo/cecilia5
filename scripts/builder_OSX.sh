#####################################
# Cecilia5 OSX standalone application
# builder script.
#
# Olivier Belanger, 2020
#####################################

export DMG_DIR="Cecilia5 5.4.1"
export DMG_NAME="Cecilia5_5.4.1.dmg"

: "${PYTHON:=python3}"
PY_VER=$($PYTHON -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
$PYTHON setup.py py2app --plist=scripts/info.plist

rm -rf build
mv dist Cecilia5_OSX

if cd Cecilia5_OSX;
then
    find . -name .git -depth -exec rm -rf {} \
    find . -name *.pyc -depth -exec rm -f {} \
    find . -name .* -depth -exec rm -f {} \;
else
    echo "Something wrong. Cecilia5_OSX not created"
    exit;
fi

rm Cecilia5.app/Contents/Resources/Cecilia5.ico
rm Cecilia5.app/Contents/Resources/CeciliaFileIcon5.ico

# universal build on recent macOS
if command -v lipo >/dev/null; then
    lipo -create Cecilia5.app/Contents/MacOS/Cecilia5 -output Cecilia5.app/Contents/MacOS/Cecilia5.universal 2>/dev/null && \
    mv Cecilia5.app/Contents/MacOS/Cecilia5.universal Cecilia5.app/Contents/MacOS/Cecilia5
fi

# Fixed wrong path in Info.plist
cd Cecilia5.app/Contents
PY_PATH="@executable_path/../Frameworks/Python.framework/Versions/${PY_VER}/Python"
awk -v p="$PY_PATH" '{gsub("@executable_path/../Frameworks/Python.framework/Versions/[0-9]+\.[0-9]+/Python", p)}1' Info.plist > Info.plist_tmp && mv Info.plist_tmp Info.plist
awk -v p="$PY_PATH" '{gsub("Library/Frameworks/Python.framework/Versions/[0-9]+\.[0-9]+/bin/python[0-9]+\.[0-9]+", p)}1' Info.plist > Info.plist_tmp && mv Info.plist_tmp Info.plist
awk -v p="$PY_PATH" '{gsub("/usr/local/bin/python[0-9]+\.[0-9]+", p)}1' Info.plist > Info.plist_tmp && mv Info.plist_tmp Info.plist

install_name_tool -change @loader_path/libwx_osx_cocoau_core-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_core-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_core.so
install_name_tool -change @loader_path/libwx_baseu_net-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_net-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_core.so
install_name_tool -change @loader_path/libwx_baseu-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_core.so

#install_name_tool -change @loader_path/libwx_osx_cocoau_adv-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_adv-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_adv.so
install_name_tool -change @loader_path/libwx_osx_cocoau_core-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_core-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_adv.so
install_name_tool -change @loader_path/libwx_baseu_net-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_net-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_adv.so
install_name_tool -change @loader_path/libwx_baseu-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_adv.so

install_name_tool -change @loader_path/libwx_osx_cocoau_html-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_html-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_html.so
install_name_tool -change @loader_path/libwx_osx_cocoau_core-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_core-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_html.so
install_name_tool -change @loader_path/libwx_baseu_net-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_net-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_html.so
install_name_tool -change @loader_path/libwx_baseu-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_html.so

install_name_tool -change @loader_path/libwx_osx_cocoau_html-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_html-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_richtext.so
install_name_tool -change @loader_path/libwx_osx_cocoau_core-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_core-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_richtext.so
install_name_tool -change @loader_path/libwx_baseu_net-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_net-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_richtext.so
install_name_tool -change @loader_path/libwx_baseu-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_richtext.so
install_name_tool -change @loader_path/libwx_osx_cocoau_richtext-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_richtext-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_richtext.so
#install_name_tool -change @loader_path/libwx_osx_cocoau_adv-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_adv-3.1.4.0.0.dylib Resources/lib/python3.7/lib-dynload/wx/_richtext.so

install_name_tool -change @loader_path/libwx_osx_cocoau_stc-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_stc-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_stc.so
install_name_tool -change @loader_path/libwx_osx_cocoau_core-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_core-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_stc.so
install_name_tool -change @loader_path/libwx_baseu_net-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_net-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_stc.so
install_name_tool -change @loader_path/libwx_baseu-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_stc.so

install_name_tool -change @loader_path/libwx_baseu_xml-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_xml-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_xml.so
install_name_tool -change @loader_path/libwx_osx_cocoau_core-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_core-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_xml.so
install_name_tool -change @loader_path/libwx_baseu_net-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_net-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_xml.so
install_name_tool -change @loader_path/libwx_baseu-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/_xml.so

install_name_tool -change @loader_path/libwx_osx_cocoau_core-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_osx_cocoau_core-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/siplib.so
install_name_tool -change @loader_path/libwx_baseu_net-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu_net-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/siplib.so
install_name_tool -change @loader_path/libwx_baseu-3.1.4.0.0.dylib @loader_path/../../../../../Frameworks/libwx_baseu-3.1.4.0.0.dylib Resources/lib/python${PY_VER}/lib-dynload/wx/siplib.so

install_name_tool -change @loader_path/libportaudio.2.dylib @loader_path/../../../../../Frameworks/libportaudio.2.dylib Resources/lib/python${PY_VER}/lib-dynload/pyo/_pyo.so
install_name_tool -change @loader_path/libportmidi.dylib @loader_path/../../../../../Frameworks/libportmidi.dylib Resources/lib/python${PY_VER}/lib-dynload/pyo/_pyo.so
install_name_tool -change @loader_path/liblo.7.dylib @loader_path/../../../../../Frameworks/liblo.7.dylib Resources/lib/python${PY_VER}/lib-dynload/pyo/_pyo.so
install_name_tool -change @loader_path/libsndfile.1.dylib @loader_path/../../../../../Frameworks/libsndfile.1.dylib Resources/lib/python${PY_VER}/lib-dynload/pyo/_pyo.so
install_name_tool -change @loader_path/libportaudio.2.dylib @loader_path/../../../../../Frameworks/libportaudio.2.dylib Resources/lib/python${PY_VER}/lib-dynload/pyo/_pyo64.so
install_name_tool -change @loader_path/libportmidi.dylib @loader_path/../../../../../Frameworks/libportmidi.dylib Resources/lib/python${PY_VER}/lib-dynload/pyo/_pyo64.so
install_name_tool -change @loader_path/liblo.7.dylib @loader_path/../../../../../Frameworks/liblo.7.dylib Resources/lib/python${PY_VER}/lib-dynload/pyo/_pyo64.so
install_name_tool -change @loader_path/libsndfile.1.dylib @loader_path/../../../../../Frameworks/libsndfile.1.dylib Resources/lib/python${PY_VER}/lib-dynload/pyo/_pyo64.so

cd ../../..
cp -R Cecilia5_OSX/Cecilia5.app .

echo "assembling DMG..."
mkdir "$DMG_DIR"
cd "$DMG_DIR"
cp -R ../Cecilia5.app .
ln -s /Applications .
cd ..

hdiutil create "$DMG_NAME" -srcfolder "$DMG_DIR"

rm -rf "$DMG_DIR"
rm -rf Cecilia5_OSX
rm -rf Cecilia5.app
