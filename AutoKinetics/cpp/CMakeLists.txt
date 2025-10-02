add_library(autokinetics STATIC
    core.cpp # add other source files here as needed
)

target_include_directories(autokinetics PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
