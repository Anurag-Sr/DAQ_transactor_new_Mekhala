# CMAKE generated file: DO NOT EDIT!
# Generated by "Unix Makefiles" Generator, CMake Version 2.8

#=============================================================================
# Special targets provided by cmake.

# Disable implicit rules so canonical targets will work.
.SUFFIXES:

# Remove some rules from gmake that .SUFFIXES does not remove.
SUFFIXES =

.SUFFIXES: .hpux_make_needs_suffix_list

# Suppress display of executed commands.
$(VERBOSE).SILENT:

# A target that is always out of date.
cmake_force:
.PHONY : cmake_force

#=============================================================================
# Set environment variables for the build.

# The shell in which to execute make rules.
SHELL = /bin/sh

# The CMake executable.
CMAKE_COMMAND = /usr/bin/cmake

# The command to remove a file.
RM = /usr/bin/cmake -E remove -f

# Escaping for special characters.
EQUALS = =

# The program to use to edit the cache.
CMAKE_EDIT_COMMAND = /usr/bin/ccmake

# The top-level source directory on which CMake was run.
CMAKE_SOURCE_DIR = /home/HGCAL_dev/sw/hexactrl-sw

# The top-level build directory on which CMake was run.
CMAKE_BINARY_DIR = /home/HGCAL_dev/sw/hexactrl-sw/build

# Include any dependencies generated for this target.
include CMakeFiles/ipbus-ctrl.dir/depend.make

# Include the progress variables for this target.
include CMakeFiles/ipbus-ctrl.dir/progress.make

# Include the compile flags for this target's objects.
include CMakeFiles/ipbus-ctrl.dir/flags.make

CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o: CMakeFiles/ipbus-ctrl.dir/flags.make
CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o: ../sources/server/executables/ipbus-ctrl.cxx
	$(CMAKE_COMMAND) -E cmake_progress_report /home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles $(CMAKE_PROGRESS_1)
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Building CXX object CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o"
	/usr/bin/c++   $(CXX_DEFINES) $(CXX_FLAGS) -o CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o -c /home/HGCAL_dev/sw/hexactrl-sw/sources/server/executables/ipbus-ctrl.cxx

CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.i: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Preprocessing CXX source to CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.i"
	/usr/bin/c++  $(CXX_DEFINES) $(CXX_FLAGS) -E /home/HGCAL_dev/sw/hexactrl-sw/sources/server/executables/ipbus-ctrl.cxx > CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.i

CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.s: cmake_force
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --green "Compiling CXX source to assembly CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.s"
	/usr/bin/c++  $(CXX_DEFINES) $(CXX_FLAGS) -S /home/HGCAL_dev/sw/hexactrl-sw/sources/server/executables/ipbus-ctrl.cxx -o CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.s

CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o.requires:
.PHONY : CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o.requires

CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o.provides: CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o.requires
	$(MAKE) -f CMakeFiles/ipbus-ctrl.dir/build.make CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o.provides.build
.PHONY : CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o.provides

CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o.provides.build: CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o

# Object files for target ipbus-ctrl
ipbus__ctrl_OBJECTS = \
"CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o"

# External object files for target ipbus-ctrl
ipbus__ctrl_EXTERNAL_OBJECTS = \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/common/src/zmq-helper.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/common/src/MarsData.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/common/src/HGCROCv2RawData.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/marsRndL1Amenu.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/LinkAligner.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/LinkCaptureBlockHandler.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/calibAndL1AplusTPGmenu.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/marsCalibAndL1Amenu.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/randomL1Amenu.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/MarsAccumulatorInterface.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/delayScanmenu.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/externalL1Amenu.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/calibAndL1Amenu.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/randomL1AplusTPGmenu.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/DAQManager.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/BX_or_L1A_OffsetFinder.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/dummymenu.cc.o" \
"/home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/objectlib.dir/sources/server/src/FastControlManager.cc.o"

ipbus-ctrl: CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/common/src/zmq-helper.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/common/src/MarsData.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/common/src/HGCROCv2RawData.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/marsRndL1Amenu.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/LinkAligner.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/LinkCaptureBlockHandler.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/calibAndL1AplusTPGmenu.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/marsCalibAndL1Amenu.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/randomL1Amenu.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/MarsAccumulatorInterface.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/delayScanmenu.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/externalL1Amenu.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/calibAndL1Amenu.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/randomL1AplusTPGmenu.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/DAQManager.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/BX_or_L1A_OffsetFinder.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/dummymenu.cc.o
ipbus-ctrl: CMakeFiles/objectlib.dir/sources/server/src/FastControlManager.cc.o
ipbus-ctrl: CMakeFiles/ipbus-ctrl.dir/build.make
ipbus-ctrl: /usr/lib64/libboost_thread-mt.so
ipbus-ctrl: /usr/lib64/libboost_system-mt.so
ipbus-ctrl: /usr/lib64/libboost_filesystem-mt.so
ipbus-ctrl: /usr/lib64/libboost_timer-mt.so
ipbus-ctrl: CMakeFiles/ipbus-ctrl.dir/link.txt
	@$(CMAKE_COMMAND) -E cmake_echo_color --switch=$(COLOR) --red --bold "Linking CXX executable ipbus-ctrl"
	$(CMAKE_COMMAND) -E cmake_link_script CMakeFiles/ipbus-ctrl.dir/link.txt --verbose=$(VERBOSE)

# Rule to build all files generated by this target.
CMakeFiles/ipbus-ctrl.dir/build: ipbus-ctrl
.PHONY : CMakeFiles/ipbus-ctrl.dir/build

CMakeFiles/ipbus-ctrl.dir/requires: CMakeFiles/ipbus-ctrl.dir/sources/server/executables/ipbus-ctrl.cxx.o.requires
.PHONY : CMakeFiles/ipbus-ctrl.dir/requires

CMakeFiles/ipbus-ctrl.dir/clean:
	$(CMAKE_COMMAND) -P CMakeFiles/ipbus-ctrl.dir/cmake_clean.cmake
.PHONY : CMakeFiles/ipbus-ctrl.dir/clean

CMakeFiles/ipbus-ctrl.dir/depend:
	cd /home/HGCAL_dev/sw/hexactrl-sw/build && $(CMAKE_COMMAND) -E cmake_depends "Unix Makefiles" /home/HGCAL_dev/sw/hexactrl-sw /home/HGCAL_dev/sw/hexactrl-sw /home/HGCAL_dev/sw/hexactrl-sw/build /home/HGCAL_dev/sw/hexactrl-sw/build /home/HGCAL_dev/sw/hexactrl-sw/build/CMakeFiles/ipbus-ctrl.dir/DependInfo.cmake --color=$(COLOR)
.PHONY : CMakeFiles/ipbus-ctrl.dir/depend

