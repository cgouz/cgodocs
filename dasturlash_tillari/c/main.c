#include "raylib.h"

int main(void)
{
    const int screenWidth = 1280;
    const int screenHeight = 720;

    InitWindow(screenWidth, screenHeight, "Airplane Game");

    Camera3D camera = {
        .position = { 10.0f, 10.0f, 10.0f },
        .target = { 0.0f, 0.0f, 0.0f },
        .up = { 0.0f, 1.0f, 0.0f },
        .fovy = 45.0f,
        .projection = CAMERA_PERSPECTIVE
    };

    SetTargetFPS(60);

    while (!WindowShouldClose())
    {
        BeginDrawing();

        ClearBackground(SKYBLUE);

        BeginMode3D(camera);

        DrawCube(
            (Vector3){ 0.0f, 0.0f, 0.0f },
            2.0f,
            2.0f,
            2.0f,
            RED
        );

        DrawGrid(20, 1.0f);

        EndMode3D();

        DrawText(
            "Step 1 - 3D World",
            20,
            20,
            30,
            WHITE
        );

        EndDrawing();
    }

    CloseWindow();

    return 0;
}