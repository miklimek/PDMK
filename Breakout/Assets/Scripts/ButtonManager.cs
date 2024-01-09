using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

public class ButtonManager : MonoBehaviour
{
    public void startKeyboard()
    {
        SceneManager.LoadScene("Keyboard");
    }

    public void startGestures()
    {
        SceneManager.LoadScene("Gestures");
    }

    public void startTangible()
    {
        SceneManager.LoadScene("Tangible");
    }

    public void startMultimodal()
    {
        SceneManager.LoadScene("Multimodal");
    }

    public void restart()
    {
        SceneManager.LoadScene("Menu");
    }
}
